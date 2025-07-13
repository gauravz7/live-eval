import asyncio
import json
import base64
import os
import time
import wave
from datetime import datetime
from google import genai
from google.genai import types
from config import *
from tools import TOOLS_DEFINITION
import config

# Record program start time
PROGRAM_START_TIME = time.time()
print(f"🚀 PROGRAM STARTED at {PROGRAM_START_TIME:.3f}")

# Initialize Google client
client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

# Configuration
CONFIG = {
    "response_modalities": ["AUDIO"], 
    "tools": [{"google_search": {}}, {"function_declarations": TOOLS_DEFINITION}],
    "system_instruction": SYSTEM_INSTRUCTION,
    "output_audio_transcription": {},
    "input_audio_transcription": {},
    "realtime_input_config": {
        "automatic_activity_detection": {
            "disabled": False,
            "start_of_speech_sensitivity": types.StartSensitivity.START_SENSITIVITY_LOW,
            "end_of_speech_sensitivity": types.EndSensitivity.END_SENSITIVITY_LOW,
            "prefix_padding_ms": 400,
            "silence_duration_ms": 400,
        }
    },
}

class SessionData:
    """Container for session data to be logged at the end"""
    def __init__(self, test_id):
        self.test_id = test_id
        self.timestamp_utc = time.time()
        self.tool_calls = []
        self.model_transcription = ""
        self.user_transcription = ""
        
    def add_tool_call(self, name, args, exec_time):
        self.tool_calls.append({"tool_name": name, "arguments": args, "execution_time_ms": exec_time})
        
    def finalize_and_log(self):
        """Log all session data as final step before disconnection"""
        try:
            # Log each tool call or NO_TOOL_CALLED marker
            calls_to_log = self.tool_calls if self.tool_calls else [{"tool_name": "NO_TOOL_CALLED", "arguments": None, "execution_time_ms": 0}]
            
            for call in calls_to_log:
                log_entry = {
                    "test_id": self.test_id,
                    "timestamp_utc": self.timestamp_utc,
                    "model_response_transcription": self.model_transcription.strip(),
                    "user_input_transcription": self.user_transcription.strip(),
                    **call
                }
                with open(config.SERVER_LOG_FILE, "a") as f:
                    f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                print(f"📝 FINAL LOG: {call['tool_name']}")
        except Exception as e:
            print(f"❌ CRITICAL: Failed to log session data: {e}")

class LiveAPIWebSocketServer(BaseWebSocketServer):
    def __init__(self, host="0.0.0.0", port=8765, save_audio_files=True):
        super().__init__(host, port)
        self.session = None
        self.save_audio_files = save_audio_files

    async def safe_send(self, websocket, message):
        """Safely send WebSocket message"""
        try:
            if hasattr(websocket, 'open') and websocket.open:
                await websocket.send(json.dumps(message, ensure_ascii=False) if isinstance(message, dict) else message)
                return True
        except Exception as e:
            print(f"⚠️ WebSocket send error: {e}")
        return False

    async def handle_tool_calls(self, response, session_data):
        """Handle tool calls and store in session data"""
        if not response.tool_call:
            return
            
        function_responses = []
        for fc in response.tool_call.function_calls:
            start_time = time.time()
            print(f"🛠️ Executing tool: {fc.name}")
            
            # Store tool call data
            session_data.add_tool_call(
                fc.name, 
                fc.args if hasattr(fc, 'args') and fc.args else None,
                round((time.time() - start_time) * 1000, 2)
            )
            
            function_responses.append(types.FunctionResponse(
                id=fc.id, name=fc.name, response={"result": "Function executed successfully"}
            ))

        try:
            await self.session.send_tool_response(function_responses=function_responses)
            print(f"📤 Sent {len(function_responses)} function responses")
        except Exception as e:
            print(f"❌ Failed to send function responses: {e}")

    def setup_audio_recording(self):
        """Setup audio recording files"""
        wave_files = {"input": None, "output": None}
        if not self.save_audio_files:
            return wave_files
            
        try:
            os.makedirs(config.RESULTS_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Input audio recording
            input_file = os.path.join(config.RESULTS_DIR, f"received_audio_{timestamp}.wav")
            wave_files["input"] = wave.open(input_file, 'wb')
            wave_files["input"].setnchannels(1)
            wave_files["input"].setsampwidth(2)
            wave_files["input"].setframerate(SEND_SAMPLE_RATE)
            
            # Output audio recording
            output_file = os.path.join(config.RESULTS_DIR, f"model_output_audio_{timestamp}.wav")
            wave_files["output"] = wave.open(output_file, 'wb')
            wave_files["output"].setnchannels(1)
            wave_files["output"].setsampwidth(2)
            wave_files["output"].setframerate(24000)
            
            print(f"🎤 Recording audio to: {input_file} & {output_file}")
        except Exception as e:
            print(f"❌ Audio recording setup failed: {e}")
        return wave_files

    async def process_audio(self, websocket, client_id):
        startup_time = (time.time() - PROGRAM_START_TIME) * 1000
        print(f"🔌 WEBSOCKET READY! Startup time: {startup_time:.2f}ms")
        
        # Initialize variables
        session_data = None
        turn_start_time = None
        first_token_received = False
        turn_count = 0
        audio_buffer = bytearray()
        wave_files = self.setup_audio_recording()
        
        self.active_clients[client_id] = websocket

        try:
            #print ("MODEL :", MODEL )
            async with client.aio.live.connect(model=MODEL, config=CONFIG) as session:
                self.session = session
                
                async with asyncio.TaskGroup() as tg:
                    
                    async def handle_messages():
                        nonlocal session_data, turn_start_time, first_token_received, audio_buffer
                        
                        async for message in websocket:
                            try:
                                data = json.loads(message)
                                msg_type = data.get("type")
                                
                                if msg_type == "start_test":
                                    session_data = SessionData(data.get("test_id"))
                                    print(f"🆔 Test started: {session_data.test_id}")
                                    
                                elif msg_type == "audio":
                                    audio_bytes = base64.b64decode(data.get("data", ""))
                                    audio_buffer.extend(audio_bytes)
                                    
                                    # Record input audio
                                    if wave_files["input"]:
                                        wave_files["input"].writeframes(audio_bytes)
                                    
                                    # Send to Gemini
                                    await session.send_realtime_input(
                                        audio=types.Blob(data=audio_bytes, mime_type=f"audio/pcm;rate={SEND_SAMPLE_RATE}")
                                    )
                                    
                                elif msg_type == "end":
                                    print("📨 End signal received")
                                    # Send buffered audio
                                    if audio_buffer:
                                        await session.send_realtime_input(
                                            audio=types.Blob(data=bytes(audio_buffer), mime_type=f"audio/pcm;rate={SEND_SAMPLE_RATE}")
                                        )
                                        audio_buffer.clear()
                                    
                                    if not turn_start_time:
                                        turn_start_time = time.time()
                                        first_token_received = False
                                        print(f"🎤 TTFT timer started")
                                        
                                elif msg_type == "ping":
                                    await self.safe_send(websocket, {"type": "pong"})
                                    
                            except Exception as e:
                                print(f"⚠️ Message processing error: {e}")

                    async def handle_responses():
                        nonlocal turn_start_time, first_token_received, turn_count, session_data
                        
                        while True:
                            turn = session.receive()
                            async for response in turn:
                                
                                # Handle tool calls
                                if response.tool_call and session_data:
                                    await self.handle_tool_calls(response, session_data)

                                # Handle server content
                                if response.server_content:
                                    sc = response.server_content
                                    
                                    # Handle interruption
                                    if hasattr(sc, "interrupted") and sc.interrupted:
                                        await self.safe_send(websocket, {"type": "interrupted", "data": "Response interrupted"})
                                    
                                    # Handle transcriptions
                                    if sc.output_transcription and sc.output_transcription.text:
                                        text = sc.output_transcription.text.strip()
                                        if text:
                                            if session_data:
                                                session_data.model_transcription += text + " "
                                            
                                            # TTFT calculation
                                            if turn_start_time and not first_token_received:
                                                ttft = (time.time() - turn_start_time) * 1000
                                                print(f"📝 TTFT: {ttft:.2f}ms")
                                                first_token_received = True
                                            
                                            await self.safe_send(websocket, {"type": "otext", "data": text})
                                    
                                    if sc.input_transcription and sc.input_transcription.text:
                                        text = sc.input_transcription.text.strip()
                                        if text:
                                            if session_data:
                                                session_data.user_transcription += text + " "
                                            
                                            if not turn_start_time:
                                                turn_start_time = time.time()
                                                turn_count += 1
                                                print(f"🎤 TURN {turn_count}: VAD detected")
                                            
                                            await self.safe_send(websocket, {"type": "itext", "data": text})
                                    
                                    # Handle turn completion
                                    if sc.turn_complete:
                                        if turn_start_time and first_token_received:
                                            total_time = (time.time() - turn_start_time) * 1000
                                            print(f"✅ TURN {turn_count} COMPLETE: {total_time:.2f}ms")
                                        
                                        await self.safe_send(websocket, {"type": "turn_complete"})
                                        
                                        # CRITICAL: Final logging before disconnection
                                        print("📝 Performing final logging...")
                                        if session_data:
                                            session_data.finalize_and_log()
                                        
                                        print("✅ Session complete, disconnecting")
                                        return

                                # Handle audio data
                                if response.data:
                                    if turn_start_time and not first_token_received:
                                        ttft = (time.time() - turn_start_time) * 1000
                                        print(f"⚡ AUDIO TTFT: {ttft:.2f}ms")
                                        first_token_received = True
                                    
                                    # Record output audio
                                    if wave_files["output"]:
                                        wave_files["output"].writeframes(response.data)
                                    
                                    # Send to client
                                    b64_audio = base64.b64encode(response.data).decode('utf-8')
                                    await self.safe_send(websocket, {"type": "audio", "data": b64_audio})

                    # Start both tasks
                    tg.create_task(handle_messages())
                    tg.create_task(handle_responses())

            await websocket.close(code=1000, reason="Turn complete")

        except Exception as e:
            print(f"❌ Critical error: {e}")
            await self.safe_send(websocket, {"type": "error", "data": f"Server error: {str(e)}"})
        finally:
            # Close audio files
            for wave_file in wave_files.values():
                if wave_file:
                    wave_file.close()
            print("✅ Audio recording finished")

async def main(model: str, save_audio: bool = True):
    main_start_time = (time.time() - PROGRAM_START_TIME) * 1000
    print(f"⏰ Reached main() in {main_start_time:.2f}ms")
    print("🚀 Starting WebSocket server...")
    print(f"🛠️ Available tools: {[tool['name'] for tool in TOOLS_DEFINITION]}")
    
    server = LiveAPIWebSocketServer(save_audio_files=save_audio)
    global MODEL
    MODEL = model
    await server.start()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default=config.MODEL, help="The model to use for the server.")
    parser.add_argument("--no-save-audio", action="store_false", dest="save_audio")
    args = parser.parse_args()

    try:
        asyncio.run(main(model=args.model, save_audio=args.save_audio))
    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
