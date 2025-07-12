"""
Google Gemini Live API WebSocket Server

This server creates a real-time audio conversation interface with Google's Gemini Live API.
It handles bidirectional audio streaming, transcription, tool calls, and comprehensive logging.

Key Features:
- Real-time audio processing with Voice Activity Detection (VAD)
- Automatic transcription of both user input and AI responses
- Tool/function calling capabilities with execution tracking
- Comprehensive session logging for evaluation purposes
- Audio file recording for analysis
- Unicode support for international languages

Flow:
1. Client connects via WebSocket
2. Audio streams bidirectionally between client and Gemini
3. Gemini processes audio and responds with audio + transcription
4. Tool calls are executed and logged
5. Complete session data is logged before disconnection
"""

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

# Record program start time for performance tracking
PROGRAM_START_TIME = time.time()
print(f"🚀 PROGRAM STARTED at {PROGRAM_START_TIME:.3f}")

# Initialize Google Gemini client with Vertex AI authentication
client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

# Gemini Live API Configuration
CONFIG = {
    "response_modalities": ["AUDIO"],  # Only audio responses (no text-only)
    "tools": [
        {"google_search": {}},  # Enable Google Search capability
        {"function_declarations": TOOLS_DEFINITION}  # Custom tools from tools.py
    ],
    "system_instruction": SYSTEM_INSTRUCTION,  # AI behavior instructions
    "output_audio_transcription": {},  # Enable transcription of AI speech
    "input_audio_transcription": {},   # Enable transcription of user speech
    "realtime_input_config": {
        "automatic_activity_detection": {  # Voice Activity Detection settings
            "disabled": False,  # Enable automatic speech detection
            "start_of_speech_sensitivity": types.StartSensitivity.START_SENSITIVITY_LOW,
            "end_of_speech_sensitivity": types.EndSensitivity.END_SENSITIVITY_LOW,
            "prefix_padding_ms": 400,      # Audio padding before speech
            "silence_duration_ms": 400,    # Silence duration to end speech
        }
    },
}

class SessionData:
    """
    Container for all session data that will be logged at the end.
    
    This class accumulates all conversation data throughout the session:
    - Tool calls with execution times
    - Complete transcriptions (user + AI)
    - Session metadata
    
    The data is only written to disk once at the end to ensure completeness.
    """
    def __init__(self, test_id):
        self.test_id = test_id                    # Unique identifier for this test session
        self.timestamp_utc = time.time()          # Session start timestamp
        self.tool_calls = []                      # List of all tool calls made
        self.model_transcription = ""             # AI's complete speech transcription
        self.user_transcription = ""              # User's complete speech transcription
        
    def add_tool_call(self, name, args, exec_time):
        """Store a tool call for later logging"""
        self.tool_calls.append({
            "tool_name": name, 
            "arguments": args, 
            "execution_time_ms": exec_time
        })
        
    def finalize_and_log(self):
        """
        Write all session data to log file as the final step before disconnection.
        
        This ensures we capture complete transcriptions and all tool calls.
        If no tools were called, logs a 'NO_TOOL_CALLED' marker to maintain log consistency.
        """
        try:
            # Determine what to log: actual tool calls or NO_TOOL_CALLED marker
            calls_to_log = self.tool_calls if self.tool_calls else [
                {"tool_name": "NO_TOOL_CALLED", "arguments": None, "execution_time_ms": 0}
            ]
            
            # Write each tool call (or marker) as a separate JSONL entry
            for call in calls_to_log:
                log_entry = {
                    "test_id": self.test_id,
                    "timestamp_utc": self.timestamp_utc,
                    "model_response_transcription": self.model_transcription.strip(),
                    "user_input_transcription": self.user_transcription.strip(),
                    **call  # Spread the tool call data
                }
                
                # Write to JSONL file with Unicode support
                with open(config.SERVER_LOG_FILE, "a") as f:
                    f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
                print(f"📝 FINAL LOG: {call['tool_name']}")
                
        except Exception as e:
            print(f"❌ CRITICAL: Failed to log session data: {e}")

class LiveAPIWebSocketServer(BaseWebSocketServer):
    """
    WebSocket server that bridges client audio with Google Gemini Live API.
    
    This server:
    1. Accepts WebSocket connections from clients
    2. Streams audio bidirectionally with Gemini Live API
    3. Handles tool/function calls
    4. Records audio files for analysis
    5. Logs comprehensive session data
    
    Each session is limited to one conversation turn for evaluation purposes.
    """
    def __init__(self, host="0.0.0.0", port=8765, save_audio_files=True):
        super().__init__(host, port)
        self.session = None                       # Gemini Live API session
        self.save_audio_files = save_audio_files  # Whether to record audio files

    async def safe_send(self, websocket, message):
        """
        Safely send a message via WebSocket with error handling.
        
        Args:
            websocket: The WebSocket connection
            message: Dict or string message to send
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        try:
            if hasattr(websocket, 'open') and websocket.open:
                # Convert dict to JSON string if needed, with Unicode support
                if isinstance(message, dict):
                    message = json.dumps(message, ensure_ascii=False)
                await websocket.send(message)
                return True
        except Exception as e:
            print(f"⚠️ WebSocket send error: {e}")
        return False

    async def handle_tool_calls(self, response, session_data):
        """
        Process tool/function calls from Gemini and store execution data.
        
        When Gemini wants to call a function (like Google Search), this method:
        1. Executes the function
        2. Measures execution time
        3. Stores the call data for later logging
        4. Returns the result to Gemini
        
        Args:
            response: Gemini response containing tool calls
            session_data: SessionData object to store call information
        """
        if not response.tool_call:
            return
            
        function_responses = []
        
        # Process each function call in the response
        for fc in response.tool_call.function_calls:
            start_time = time.time()
            print(f"🛠️ Executing tool: {fc.name}")
            
            # Store tool call data in session (actual execution happens elsewhere)
            session_data.add_tool_call(
                fc.name, 
                fc.args if hasattr(fc, 'args') and fc.args else None,
                round((time.time() - start_time) * 1000, 2)  # Execution time in ms
            )
            
            # Create response for Gemini
            function_responses.append(types.FunctionResponse(
                id=fc.id, 
                name=fc.name, 
                response={"result": "Function executed successfully"}
            ))

        # Send all function responses back to Gemini
        try:
            await self.session.send_tool_response(function_responses=function_responses)
            print(f"📤 Sent {len(function_responses)} function responses")
        except Exception as e:
            print(f"❌ Failed to send function responses: {e}")

    def setup_audio_recording(self):
        """
        Set up WAV file recording for both input (user) and output (AI) audio.
        
        Creates timestamped WAV files in the results directory for:
        - User audio input (16kHz, 16-bit)  
        - AI audio output (24kHz, 16-bit)
        
        Returns:
            dict: Contains 'input' and 'output' wave file objects (or None if disabled)
        """
        wave_files = {"input": None, "output": None}
        if not self.save_audio_files:
            return wave_files
            
        try:
            # Ensure results directory exists
            os.makedirs(config.RESULTS_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Setup input audio recording (user speech)
            input_file = os.path.join(config.RESULTS_DIR, f"received_audio_{timestamp}.wav")
            wave_files["input"] = wave.open(input_file, 'wb')
            wave_files["input"].setnchannels(1)      # Mono
            wave_files["input"].setsampwidth(2)      # 16-bit
            wave_files["input"].setframerate(SEND_SAMPLE_RATE)  # Match client rate
            
            # Setup output audio recording (AI speech)
            output_file = os.path.join(config.RESULTS_DIR, f"model_output_audio_{timestamp}.wav")
            wave_files["output"] = wave.open(output_file, 'wb')
            wave_files["output"].setnchannels(1)     # Mono
            wave_files["output"].setsampwidth(2)     # 16-bit  
            wave_files["output"].setframerate(24000) # Gemini's output rate
            
            print(f"🎤 Recording audio to: {input_file} & {output_file}")
        except Exception as e:
            print(f"❌ Audio recording setup failed: {e}")
        return wave_files

    async def process_audio(self, websocket, client_id):
        """
        Main processing function for each WebSocket connection.
        
        This function:
        1. Establishes connection with Gemini Live API
        2. Sets up audio recording
        3. Manages two concurrent tasks:
           - handle_messages(): Processes incoming WebSocket messages
           - handle_responses(): Processes Gemini responses
        4. Ensures session data is logged before disconnection
        
        The session is limited to one conversation turn for evaluation purposes.
        """
        # Calculate and log startup performance
        startup_time = (time.time() - PROGRAM_START_TIME) * 1000
        print(f"🔌 WEBSOCKET READY! Startup time: {startup_time:.2f}ms")
        
        # Initialize session variables
        session_data = None                # Will store all conversation data
        turn_start_time = None            # Time when user finished speaking
        first_token_received = False      # Whether we've received first AI response
        turn_count = 0                    # Number of conversation turns
        audio_buffer = bytearray()        # Buffer for collecting audio chunks
        wave_files = self.setup_audio_recording()  # Setup audio file recording
        
        # Register this client
        self.active_clients[client_id] = websocket

        try:
            # Connect to Gemini Live API
            async with client.aio.live.connect(model=MODEL, config=CONFIG) as session:
                self.session = session  # Store session reference for tool calls
                
                # Run two concurrent tasks for bidirectional communication
                async with asyncio.TaskGroup() as tg:
                    
                    async def handle_messages():
                        """
                        Task 1: Process incoming WebSocket messages from client.
                        
                        Handles:
                        - start_test: Initialize session with test ID
                        - audio: Forward audio data to Gemini
                        - end: Signal end of user speech, start TTFT timer
                        - ping: Keep connection alive
                        """
                        nonlocal session_data, turn_start_time, first_token_received, audio_buffer
                        
                        async for message in websocket:
                            try:
                                data = json.loads(message)
                                msg_type = data.get("type")
                                
                                if msg_type == "start_test":
                                    # Initialize new session with test identifier
                                    session_data = SessionData(data.get("test_id"))
                                    print(f"🆔 Test started: {session_data.test_id}")
                                    
                                elif msg_type == "audio":
                                    # Receive audio data from client and forward to Gemini
                                    audio_bytes = base64.b64decode(data.get("data", ""))
                                    audio_buffer.extend(audio_bytes)  # Buffer for end signal
                                    
                                    # Record incoming audio for analysis
                                    if wave_files["input"]:
                                        wave_files["input"].writeframes(audio_bytes)
                                    
                                    # Forward audio to Gemini Live API
                                    await session.send_realtime_input(
                                        audio=types.Blob(
                                            data=audio_bytes, 
                                            mime_type=f"audio/pcm;rate={SEND_SAMPLE_RATE}"
                                        )
                                    )
                                    
                                elif msg_type == "end":
                                    # Client signals end of speech - start TTFT measurement
                                    print("📨 End signal received")
                                    
                                    # Send any remaining buffered audio to Gemini
                                    if audio_buffer:
                                        await session.send_realtime_input(
                                            audio=types.Blob(
                                                data=bytes(audio_buffer), 
                                                mime_type=f"audio/pcm;rate={SEND_SAMPLE_RATE}"
                                            )
                                        )
                                        audio_buffer.clear()
                                    
                                    # Start Time-To-First-Token measurement
                                    if not turn_start_time:
                                        turn_start_time = time.time()
                                        first_token_received = False
                                        print(f"🎤 TTFT timer started")
                                        
                                elif msg_type == "ping":
                                    # Respond to keepalive ping
                                    await self.safe_send(websocket, {"type": "pong"})
                                    
                            except Exception as e:
                                print(f"⚠️ Message processing error: {e}")

                    async def handle_responses():
                        """
                        Task 2: Process responses from Gemini Live API.
                        
                        Handles:
                        - Tool calls: Execute functions and store results
                        - Transcriptions: Capture both user and AI speech-to-text
                        - Audio data: Forward AI speech to client
                        - Turn completion: Trigger final logging and disconnection
                        """
                        nonlocal turn_start_time, first_token_received, turn_count, session_data
                        
                        while True:
                            # Get the next turn from Gemini
                            turn = session.receive()
                            
                            # Process each response in this turn
                            async for response in turn:
                                
                                # Handle tool/function calls from Gemini
                                if response.tool_call and session_data:
                                    await self.handle_tool_calls(response, session_data)

                                # Process server content (transcriptions, audio, etc.)
                                if response.server_content:
                                    sc = response.server_content  # Shorthand for readability
                                    
                                    # Handle interruption (user started speaking while AI was talking)
                                    if hasattr(sc, "interrupted") and sc.interrupted:
                                        await self.safe_send(websocket, {
                                            "type": "interrupted", 
                                            "data": "Response interrupted"
                                        })
                                    
                                    # Handle AI speech transcription (speech-to-text of AI response)
                                    if sc.output_transcription and sc.output_transcription.text:
                                        text = sc.output_transcription.text.strip()
                                        if text:
                                            # Store transcription in session data
                                            if session_data:
                                                session_data.model_transcription += text + " "
                                            
                                            # Calculate Time-To-First-Token for text
                                            if turn_start_time and not first_token_received:
                                                ttft = (time.time() - turn_start_time) * 1000
                                                print(f"📝 TTFT: {ttft:.2f}ms")
                                                first_token_received = True
                                            
                                            # Send transcription to client
                                            await self.safe_send(websocket, {
                                                "type": "otext", "data": text
                                            })
                                    
                                    # Handle user speech transcription (speech-to-text of user input)
                                    if sc.input_transcription and sc.input_transcription.text:
                                        text = sc.input_transcription.text.strip()
                                        if text:
                                            # Store transcription in session data
                                            if session_data:
                                                session_data.user_transcription += text + " "
                                            
                                            # Start TTFT timer when VAD detects end of user speech
                                            if not turn_start_time:
                                                turn_start_time = time.time()
                                                turn_count += 1
                                                print(f"🎤 TURN {turn_count}: VAD detected")
                                            
                                            # Send transcription to client
                                            await self.safe_send(websocket, {
                                                "type": "itext", "data": text
                                            })
                                    
                                    # Handle turn completion - this ends the session
                                    if sc.turn_complete:
                                        # Calculate total response time
                                        if turn_start_time and first_token_received:
                                            total_time = (time.time() - turn_start_time) * 1000
                                            print(f"✅ TURN {turn_count} COMPLETE: {total_time:.2f}ms")
                                        
                                        # Notify client that turn is complete
                                        await self.safe_send(websocket, {"type": "turn_complete"})
                                        
                                        # CRITICAL: Perform final logging before disconnection
                                        print("📝 Performing final logging...")
                                        if session_data:
                                            session_data.finalize_and_log()
                                        
                                        print("✅ Session complete, disconnecting")
                                        return  # Exit to close session

                                # Handle audio data from Gemini (AI speech)
                                if response.data:
                                    # Calculate Time-To-First-Token for audio
                                    if turn_start_time and not first_token_received:
                                        ttft = (time.time() - turn_start_time) * 1000
                                        print(f"⚡ AUDIO TTFT: {ttft:.2f}ms")
                                        first_token_received = True
                                    
                                    # Record AI audio output for analysis
                                    if wave_files["output"]:
                                        wave_files["output"].writeframes(response.data)
                                    
                                    # Send audio to client (encode as base64)
                                    b64_audio = base64.b64encode(response.data).decode('utf-8')
                                    await self.safe_send(websocket, {
                                        "type": "audio", "data": b64_audio
                                    })

                    # Start both tasks concurrently
                    tg.create_task(handle_messages())
                    tg.create_task(handle_responses())

            # Close WebSocket connection cleanly
            await websocket.close(code=1000, reason="Turn complete")

        except Exception as e:
            print(f"❌ Critical error: {e}")
            await self.safe_send(websocket, {
                "type": "error", 
                "data": f"Server error: {str(e)}"
            })
        finally:
            # Clean up: close audio recording files
            for wave_file in wave_files.values():
                if wave_file:
                    wave_file.close()
            print("✅ Audio recording finished")                                session_data.model_transcription += text + " "
                                            
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

async def main(save_audio: bool = True):
    main_start_time = (time.time() - PROGRAM_START_TIME) * 1000
    print(f"⏰ Reached main() in {main_start_time:.2f}ms")
    print("🚀 Starting WebSocket server...")
    print(f"🛠️ Available tools: {[tool['name'] for tool in TOOLS_DEFINITION]}")
    
    server = LiveAPIWebSocketServer(save_audio_files=save_audio)
    await server.start()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-save-audio", action="store_false", dest="save_audio")
    args = parser.parse_args()

    try:
        asyncio.run(main(save_audio=args.save_audio))
    except KeyboardInterrupt:
        print("Exiting...")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()