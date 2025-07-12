import asyncio
import json
import base64
import os
import time
import wave
from datetime import datetime

# Record program start time
PROGRAM_START_TIME = time.time()
print(f"🚀 PROGRAM STARTED at {PROGRAM_START_TIME:.3f}")

# Import Google Generative AI components
print("🔧 Initializing Google Generative AI client...")
client_init_start = time.time()
from google import genai
from google.genai import types  # CRITICAL: Import types for new API format
from google.genai.types import (
    LiveConnectConfig,
    SpeechConfig,
    VoiceConfig,
    PrebuiltVoiceConfig,
)

# Import common components
from config import (
    BaseWebSocketServer,
    logger,
    PROJECT_ID,
    LOCATION,
    MODEL,
    VOICE_NAME,
    SEND_SAMPLE_RATE,
    SYSTEM_INSTRUCTION,
)
from tools import TOOLS_DEFINITION
import config

# Initialize Google client
client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)
client_init_time = (time.time() - client_init_start) * 1000
print(f"✅ Google client initialized in {client_init_time:.2f}ms")


# Combined tools configuration
tools = [
    {"google_search": {}},  # Google Search tool
    {"function_declarations": TOOLS_DEFINITION}
]

CONFIG = {
    "response_modalities": ["AUDIO"], 
    "tools": tools,
    "system_instruction": SYSTEM_INSTRUCTION,
    # Audio transcription settings
    "output_audio_transcription": {},  # Enable transcription of model's audio output
    "input_audio_transcription": {},   # Enable transcription of user's audio input
    # Voice Activity Detection (VAD) configuration
    "realtime_input_config": {
        "automatic_activity_detection": {
            "disabled": False,  # Enable automatic VAD
            "start_of_speech_sensitivity": types.StartSensitivity.START_SENSITIVITY_LOW,  # Less sensitive
            "end_of_speech_sensitivity": types.EndSensitivity.END_SENSITIVITY_LOW,        # Less sensitive
            "prefix_padding_ms": 400,      # More audio padding before speech starts
            "silence_duration_ms": 400,  # Longer silence before considering speech ended
        }
    },
}

class LiveAPIWebSocketServer(BaseWebSocketServer):
    """WebSocket server implementation using Gemini LiveAPI directly."""

    def __init__(self, host="0.0.0.0", port=8765, save_audio_files=True):
        super().__init__(host, port)
        self.session = None
        self.current_test_id = None
        self.save_audio_files = save_audio_files

    async def safe_websocket_send(self, websocket, message):
        """Safely send message to WebSocket with error handling"""
        try:
            if hasattr(websocket, 'open') and websocket.open:
                if isinstance(message, dict):
                    message = json.dumps(message)
                await websocket.send(message)
                return True
            else:
                print(f"⚠️ WebSocket not open, skipping message")
                return False
        except Exception as e:
            print(f"⚠️ WebSocket send error: {e}")
            return False

    async def handle_tool_calls(self, response, websocket, model_transcription):
        """Handle tool calls from the Gemini model - FIXED with error handling"""
        if response.tool_call:
            tool_call_start = time.time()
            function_responses = []
            
            print(f"\n🔧 Processing {len(response.tool_call.function_calls)} tool call(s)")
            
            for fc in response.tool_call.function_calls:
                func_start = time.time()
                print(f"🛠️ Executing tool: {fc.name}")
                
                response_data = {"result": "Function executed successfully"}

                # --- START: Required modification for logging ---
                log_entry = {
                    "test_id": self.current_test_id,
                    "timestamp_utc": time.time(),
                    "tool_name": fc.name,
                    "arguments": fc.args if hasattr(fc, 'args') and fc.args else None,
                    "execution_time_ms": round((time.time() - func_start) * 1000, 2),
                    "model_response_transcription": model_transcription.strip()
                }
                
                # Log the function call to the shared log file
                try:
                    with open(config.SERVER_LOG_FILE, "a") as f:
                        f.write(json.dumps(log_entry) + "\n")
                    print(f"📝 Logged function call: {fc.name} (took {(time.time() - func_start) * 1000:.2f}ms)")
                except Exception as log_error:
                    print(f"❌ Failed to log function call: {log_error}")
                # --- END: Required modification for logging ---
                
                function_response = types.FunctionResponse(
                    id=fc.id,
                    name=fc.name,
                    response=response_data
                )
                function_responses.append(function_response)

            # Send tool responses back to the session
            try:
                await self.session.send_tool_response(function_responses=function_responses)
                print(f"📤 Sent function responses to Gemini")
            except Exception as e:
                print(f"❌ Failed to send function responses: {e}")
            
            total_tool_time = (time.time() - tool_call_start) * 1000
            print(f"🔧 All tool calls completed in {total_tool_time:.2f}ms")

    async def process_audio(self, websocket, client_id):
        # Calculate and display startup metrics on first connection
        connection_time = time.time()
        startup_time = (connection_time - PROGRAM_START_TIME) * 1000
        print(f"🔌 WEBSOCKET READY! Total startup time: {startup_time:.2f}ms")
        
        # TTFT tracking variables
        last_audio_time = None
        turn_start_time = None
        first_token_received = False
        turn_count = 0
        
        # Store reference to client
        self.active_clients[client_id] = websocket

        # --- Audio Recording Setup ---
        wave_file = None
        if self.save_audio_files:
            try:
                os.makedirs(config.RESULTS_DIR, exist_ok=True)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                audio_filename = os.path.join(config.RESULTS_DIR, f"received_audio_{timestamp}.wav")
                
                wave_file = wave.open(audio_filename, 'wb')
                wave_file.setnchannels(1)
                wave_file.setsampwidth(2) # 16-bit
                wave_file.setframerate(SEND_SAMPLE_RATE)
                print(f"🎤 Recording incoming audio to {audio_filename}")
            except Exception as e:
                print(f"❌ Failed to set up audio recording: {e}")
                wave_file = None
        # --- End Audio Recording Setup ---

        # --- Model Output Audio Recording Setup ---
        output_wave_file = None
        if self.save_audio_files:
            try:
                # The results directory is already created above
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_audio_filename = os.path.join(config.RESULTS_DIR, f"model_output_audio_{timestamp}.wav")
                
                output_wave_file = wave.open(output_audio_filename, 'wb')
                output_wave_file.setnchannels(1)
                output_wave_file.setsampwidth(2) # 16-bit
                output_wave_file.setframerate(24000) # As per documentation
                print(f"🎤 Recording model output audio to {output_audio_filename}")
            except Exception as e:
                print(f"❌ Failed to set up model output audio recording: {e}")
                output_wave_file = None
        # --- End Model Output Audio Recording Setup ---

        try:
            # Connect to Gemini using LiveAPI
            async with client.aio.live.connect(model=MODEL, config=CONFIG) as session:
                # Store session reference for tool calls
                self.session = session
                
                # Track if we've already handled the initial session setup
                session_initialized = False
                
                # Audio buffer for collecting chunks
                audio_buffer = bytearray()
                
                async with asyncio.TaskGroup() as tg:
                    
                    # Task to process incoming WebSocket messages
                    async def handle_websocket_messages():
                        nonlocal last_audio_time, turn_start_time, first_token_received, turn_count, audio_buffer
                        
                        try:
                            async for message in websocket:
                                try:
                                    data = json.loads(message)
                                    if data.get("type") == "start_test":
                                        self.current_test_id = data.get("test_id")
                                        print(f"Starting test: {self.current_test_id}")
                                    elif data.get("type") == "audio":
                                        # Update last audio time when we receive audio from user
                                        last_audio_time = time.time()
                                        
                                        # Decode base64 audio data
                                        audio_bytes = base64.b64decode(data.get("data", ""))
                                        
                                        # --- Write to recording ---
                                        if wave_file:
                                            try:
                                                wave_file.writeframes(audio_bytes)
                                            except Exception as e:
                                                print(f"❌ Error writing to wave file: {e}")
                                        # --- End write ---
                                        
                                        # Add to buffer
                                        audio_buffer.extend(audio_bytes)
                                        
                                        # Send audio immediately using NEW API FORMAT
                                        try:
                                            await session.send_realtime_input(
                                                audio=types.Blob(
                                                    data=audio_bytes,
                                                    mime_type=f"audio/pcm;rate={SEND_SAMPLE_RATE}"
                                                )
                                            )
                                        except Exception as e:
                                            logger.error(f"Error sending audio to Gemini: {e}")
                                        
                                    elif data.get("type") == "end":
                                        # Client is done sending audio for this turn
                                        print(f"📨 RECEIVED END SIGNAL FROM CLIENT")
                                        logger.info("Received end signal from client")
                                        
                                        # Send any remaining audio in buffer
                                        if len(audio_buffer) > 0:
                                            try:
                                                await session.send_realtime_input(
                                                    audio=types.Blob(
                                                        data=bytes(audio_buffer),
                                                        mime_type=f"audio/pcm;rate={SEND_SAMPLE_RATE}"
                                                    )
                                                )
                                                print(f"📤 Sent final audio buffer: {len(audio_buffer)} bytes")
                                                audio_buffer.clear()
                                            except Exception as e:
                                                logger.error(f"Error sending final audio buffer: {e}")
                                        
                                        # Mark the start time for TTFT measurement
                                        if not turn_start_time:
                                            turn_start_time = time.time()
                                            first_token_received = False
                                            print(f"🎤 USER FINISHED SPEAKING (END SIGNAL) - TTFT timer started at {turn_start_time:.3f}")
                                            
                                    elif data.get("type") == "text":
                                        # Handle text messages
                                        logger.info(f"Received text: {data.get('data')}")
                                    
                                    elif data.get("type") == "ping":
                                        # Handle ping messages to keep connection alive
                                        await self.safe_websocket_send(websocket, {"type": "pong"})
                                        
                                except json.JSONDecodeError:
                                    logger.error("Invalid JSON message received")
                                except Exception as e:
                                    logger.error(f"Error processing message: {e}")
                        except Exception as e:
                            print(f"⚠️ WebSocket message handling error: {e}")
                            # Don't crash, just log and continue

                    # Task to receive and play responses - FIXED VERSION
                    async def receive_and_play():
                        nonlocal session_initialized, turn_start_time, first_token_received, last_audio_time, turn_count
                        
                        try:
                            while True:
                                input_transcriptions = []
                                output_transcriptions = []
                                tool_called_this_turn = False # Track if a tool was called in this turn

                                # Use the same pattern as reference code
                                turn = session.receive()
                                model_transcription = "" # Accumulate transcription for the turn
                                async for response in turn:
                                    # Handle audio transcriptions
                                    if response.server_content:
                                        # Output transcription (model's speech to text)
                                        if response.server_content.output_transcription:
                                            transcript = response.server_content.output_transcription.text
                                            if transcript and transcript.strip():
                                                model_transcription += transcript + " "
                                    
                                    # Handle tool calls with WebSocket reference
                                    if response.tool_call:
                                        tool_called_this_turn = True
                                        await self.handle_tool_calls(response, websocket, model_transcription)

                                    # Check if connection will be terminated soon
                                    if response.go_away is not None:
                                        logger.info(f"Session will terminate in: {response.go_away.time_left}")

                                    server_content = response.server_content

                                    # Handle interruption
                                    if (hasattr(server_content, "interrupted") and server_content.interrupted):
                                        logger.info("🤐 INTERRUPTION DETECTED")
                                        await self.safe_websocket_send(websocket, {
                                            "type": "interrupted",
                                            "data": "Response interrupted by user input"
                                        })

                                    # Handle audio transcriptions
                                    if response.server_content:
                                        # Output transcription (model's speech to text)
                                        if response.server_content.output_transcription:
                                            transcript = response.server_content.output_transcription.text
                                            if transcript and transcript.strip():
                                                print(f"📝 AI said: '{transcript[:50]}...'")
                                                logger.info(f"🎤 Model said: {transcript}")
                                                output_transcriptions.append(transcript)
                                                model_transcription += transcript + " "
                                                
                                                # Calculate TTFT for text
                                                if turn_start_time and not first_token_received:
                                                    ttft = (time.time() - turn_start_time) * 1000
                                                    print(f"📝 TURN {turn_count} - TIME TO FIRST TEXT TOKEN: {ttft:.2f}ms")
                                                    logger.info(f"📝 Time to First Text Token: {ttft:.2f}ms")
                                                    first_token_received = True
                                                
                                                # Send text to client
                                                await self.safe_websocket_send(websocket, {
                                                    "type": "otext",
                                                    "data": transcript
                                                })
                                        
                                        # Input transcription (user's speech to text)
                                        if response.server_content.input_transcription:
                                            transcript = response.server_content.input_transcription.text
                                            if transcript and transcript.strip():
                                                print(f"👤 User said: '{transcript}'")
                                                logger.info(f"🗣️  You said: {transcript}")
                                                input_transcriptions.append(transcript)
                                                
                                                # When we get input transcription, user just finished speaking
                                                if not turn_start_time and not first_token_received:
                                                    turn_start_time = time.time()
                                                    turn_count += 1
                                                    print(f"🎤 TURN {turn_count}: User finished speaking (VAD detected) - TTFT timer started at {turn_start_time:.3f}")
                                                
                                                await self.safe_websocket_send(websocket, {
                                                    "type": "itext",
                                                    "data": transcript
                                                })

                                    # Handle audio data
                                    if data := response.data:
                                        # Calculate TTFT if this is the first token
                                        if turn_start_time and not first_token_received:
                                            ttft = (time.time() - turn_start_time) * 1000
                                            print(f"⚡ TURN {turn_count} - TIME TO FIRST AUDIO TOKEN: {ttft:.2f}ms")
                                            logger.info(f"⚡ Time to First Token: {ttft:.2f}ms")
                                            first_token_received = True
                                        
                                        # --- Write to output recording ---
                                        if output_wave_file:
                                            try:
                                                output_wave_file.writeframes(data)
                                            except Exception as e:
                                                print(f"❌ Error writing to output wave file: {e}")
                                        # --- End write ---
                                        
                                        # Send audio to client
                                        b64_audio = base64.b64encode(data).decode('utf-8')
                                        await self.safe_websocket_send(websocket, {
                                            "type": "audio",
                                            "data": b64_audio
                                        })
                                    elif text := response.text:
                                        # Handle any text responses
                                        logger.info(f"Text response: {text}")

                                    # Handle turn completion
                                    if server_content and server_content.turn_complete:
                                        if not tool_called_this_turn:
                                            # If no tool was called, log a specific marker to maintain log integrity
                                            log_entry = {
                                                "test_id": self.current_test_id,
                                                "timestamp_utc": time.time(),
                                                "tool_name": "NO_TOOL_CALLED",
                                                "arguments": None,
                                                "execution_time_ms": 0,
                                                "model_response_transcription": model_transcription.strip()
                                            }
                                            try:
                                                with open(config.SERVER_LOG_FILE, "a") as f:
                                                    f.write(json.dumps(log_entry) + "\n")
                                                print("📝 Logged NO_TOOL_CALLED marker.")
                                            except Exception as log_error:
                                                print(f"❌ Failed to log NO_TOOL_CALLED marker: {log_error}")
                                        else:
                                            # Log the tool call just before the turn completes
                                            await self.handle_tool_calls(response, websocket, model_transcription)

                                        if turn_start_time and first_token_received:
                                            total_turn_time = (time.time() - turn_start_time) * 1000
                                            print(f"✅ TURN {turn_count} COMPLETE - Total response time: {total_turn_time:.2f}ms")
                                        else:
                                            print(f"✅ TURN {turn_count} COMPLETE - No timing data")
                                        
                                        logger.info("✅ Gemini done talking")
                                        # Reset TTFT tracking for next turn
                                        turn_start_time = None
                                        first_token_received = False
                                        await self.safe_websocket_send(websocket, {
                                            "type": "turn_complete"
                                        })
                                        
                                        # --- START: Exit after one turn ---
                                        print("✅ Turn complete. Server is closing this session and is ready for the next connection.")
                                        return  # Exit the receive_and_play task to close the session
                                        # --- END: Exit after one turn ---

                                logger.info(f"Input transcription: {''.join(input_transcriptions)}")
                                logger.info(f"Output transcription: {''.join(output_transcriptions)}")
                                
                        except Exception as e:
                            logger.error(f"Error in receive_and_play: {e}")
                            print(f"⚠️ Session error, but continuing server operation: {e}")
                            # Don't crash the entire server, just log and continue

                    # Start tasks
                    tg.create_task(handle_websocket_messages())
                    tg.create_task(receive_and_play())

            # After the task group is done, explicitly close the connection
            print("🤝 Task group finished. Closing WebSocket connection from server side.")
            await websocket.close(code=1000, reason="Turn complete")

        except Exception as e:
            logger.error(f"Critical error in process_audio: {e}")
            print(f"❌ Critical error in audio processing: {e}")
            # Try to send error to client
            await self.safe_websocket_send(websocket, {
                "type": "error",
                "data": f"Server error: {str(e)}"
            })
        finally:
            # --- Close Audio Recording ---
            if wave_file:
                wave_file.close()
                print(f"✅ Finished recording input audio.")
            if output_wave_file:
                output_wave_file.close()
                print(f"✅ Finished recording model output audio.")
            # --- End Close ---

async def main(save_audio: bool = True):
    """Main function to start the server"""
    # Calculate time to reach main execution
    main_start_time = (time.time() - PROGRAM_START_TIME) * 1000
    print(f"⏰ Reached main() in {main_start_time:.2f}ms")
    
    print("🚀 Starting WebSocket server with tools...")
    print("🛠️ Available tools:")
    for tool in TOOLS_DEFINITION:
        print(f"  - {tool['name']}")
    print(f"🎵 Audio format: 16kHz PCM (Gemini Live compatible)")
    print(f"🔧 WebSocket: Fixed error handling and connection safety")
    
    server = LiveAPIWebSocketServer(save_audio_files=save_audio)
    await server.start()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-save-audio", action="store_false", dest="save_audio", help="Disable saving audio files")
    args = parser.parse_args()

    try:
        asyncio.run(main(save_audio=args.save_audio))
    except KeyboardInterrupt:
        logger.info("Exiting application via KeyboardInterrupt...")
    except Exception as e:
        logger.error(f"Unhandled exception in main: {e}")
        import traceback
        traceback.print_exc()
