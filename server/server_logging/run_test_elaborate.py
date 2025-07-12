"""
Enhanced Test Client with Comprehensive Logging

This client runs test cases against the LiveAPI server and logs detailed information:
- Complete conversation transcripts (input/output)
- Tool calls and responses 
- Timing metrics (TTFT, total response time)
- Audio streaming details
- Server responses and errors

All data is logged on the client side for comprehensive analysis.
"""

import asyncio
import json
import os
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
import websockets
import base64
import importlib

import config
import tts_client
from google import genai

# Force reload of the config module to pick up changes
importlib.reload(config)


class TestSessionLogger:
    """
    Comprehensive logger for test session data on the client side.
    
    Captures all aspects of the conversation:
    - Test metadata and configuration
    - Audio streaming metrics
    - Real-time transcriptions
    - Tool calls and responses
    - Timing measurements
    - Final results and analysis
    """
    
    def __init__(self, log_file: str = "client_test_log.jsonl"):
        self.log_file = log_file
        self.current_session = None
        
    def start_session(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize a new test session with comprehensive tracking"""
        self.current_session = {
            # Test metadata
            "test_id": test_case.get("test_id"),
            "test_case": test_case,
            "session_start_time": time.time(),
            "session_start_timestamp": datetime.now().isoformat(),
            
            # Input data
            "spoken_text_input": test_case.get("spoken_text", ""),
            "expected_tool": test_case.get("expected_tool", ""),
            
            # Audio metrics
            "audio_total_bytes": 0,
            "audio_chunks_sent": 0,
            "audio_streaming_start_time": None,
            "audio_streaming_end_time": None,
            
            # Response tracking
            "server_responses": [],           # All raw server responses
            "input_transcriptions": [],       # User speech transcriptions
            "output_transcriptions": [],      # AI speech transcriptions
            "tool_calls_detected": [],        # Tool calls observed
            "audio_responses_received": 0,    # Count of audio chunks
            
            # Timing metrics
            "time_to_first_token": None,      # TTFT measurement
            "total_response_time": None,      # End-to-end response time
            "turn_complete_time": None,       # When turn completed
            
            # Final results
            "session_completed": False,
            "errors": [],
            "success": False
        }
        return self.current_session
    
    def log_audio_chunk(self, chunk_size: int):
        """Log audio streaming metrics"""
        if self.current_session:
            if self.current_session["audio_streaming_start_time"] is None:
                self.current_session["audio_streaming_start_time"] = time.time()
            
            self.current_session["audio_total_bytes"] += chunk_size
            self.current_session["audio_chunks_sent"] += 1
    
    def log_server_response(self, response_type: str, data: Any):
        """Log all server responses with timestamps"""
        if self.current_session:
            response_entry = {
                "timestamp": time.time(),
                "type": response_type,
                "data": data,
                "time_since_session_start": time.time() - self.current_session["session_start_time"]
            }
            self.current_session["server_responses"].append(response_entry)
    
    def log_transcription(self, transcription_type: str, text: str):
        """Log transcriptions (input/output) with timing"""
        if self.current_session:
            transcription_entry = {
                "timestamp": time.time(),
                "text": text,
                "time_since_session_start": time.time() - self.current_session["session_start_time"]
            }
            
            if transcription_type == "input":
                self.current_session["input_transcriptions"].append(transcription_entry)
            elif transcription_type == "output":
                self.current_session["output_transcriptions"].append(transcription_entry)
                
                # Calculate TTFT if this is the first output transcription
                if (self.current_session["time_to_first_token"] is None and 
                    self.current_session["audio_streaming_end_time"]):
                    ttft = (time.time() - self.current_session["audio_streaming_end_time"]) * 1000
                    self.current_session["time_to_first_token"] = ttft
    
    def log_tool_call(self, tool_name: str, arguments: Any = None):
        """Log detected tool calls"""
        if self.current_session:
            tool_call_entry = {
                "timestamp": time.time(),
                "tool_name": tool_name,
                "arguments": arguments,
                "time_since_session_start": time.time() - self.current_session["session_start_time"]
            }
            self.current_session["tool_calls_detected"].append(tool_call_entry)
    
    def log_error(self, error_message: str, error_type: str = "general"):
        """Log errors during the session"""
        if self.current_session:
            error_entry = {
                "timestamp": time.time(),
                "type": error_type,
                "message": error_message,
                "time_since_session_start": time.time() - self.current_session["session_start_time"]
            }
            self.current_session["errors"].append(error_entry)
    
    def finalize_session(self, success: bool = False):
        """Complete the session and calculate final metrics"""
        if self.current_session:
            # Mark audio streaming end time if not set
            if self.current_session["audio_streaming_end_time"] is None:
                self.current_session["audio_streaming_end_time"] = time.time()
            
            # Calculate total response time
            if self.current_session["turn_complete_time"]:
                total_time = (self.current_session["turn_complete_time"] - 
                            self.current_session["audio_streaming_end_time"]) * 1000
                self.current_session["total_response_time"] = total_time
            
            # Aggregate transcriptions
            self.current_session["complete_input_transcription"] = " ".join(
                [t["text"] for t in self.current_session["input_transcriptions"]]
            ).strip()
            
            self.current_session["complete_output_transcription"] = " ".join(
                [t["text"] for t in self.current_session["output_transcriptions"]]
            ).strip()
            
            # Mark session as completed
            self.current_session["session_completed"] = True
            self.current_session["success"] = success
            self.current_session["session_end_time"] = time.time()
            self.current_session["session_duration"] = (
                self.current_session["session_end_time"] - 
                self.current_session["session_start_time"]
            )
            
            # Write to log file
            self._write_session_to_log()
    
    def _write_session_to_log(self):
        """Write the complete session data to JSONL log file"""
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(self.current_session, ensure_ascii=False) + "\n")
            print(f"📝 Session logged to {self.log_file}")
        except Exception as e:
            print(f"❌ Failed to write session log: {e}")


def load_test_cases_from_json(file_path: str) -> List[Dict[str, Any]]:
    """Loads test cases from a JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            test_cases = json.load(f)
        print(f"✅ Successfully loaded {len(test_cases)} test cases from {file_path}")
        return test_cases
    except FileNotFoundError:
        print(f"❌ Error: Test case file not found at {file_path}")
        return []
    except json.JSONDecodeError:
        print(f"❌ Error: Could not decode JSON from {file_path}")
        return []


async def run_single_test_case(test_case: Dict[str, Any], logger: TestSessionLogger) -> bool:
    """
    Execute a single test case with comprehensive logging.
    
    Args:
        test_case: The test case configuration
        logger: Session logger instance
        
    Returns:
        bool: True if test completed successfully, False otherwise
    """
    # Initialize session logging
    session = logger.start_session(test_case)
    print(f"🚀 Starting test: {test_case['test_id']} - '{test_case['spoken_text']}'")
    
    try:
        # Generate audio from text
        print("🎤 Converting text to audio...")
        audio_content = tts_client.convert_text_to_audio(test_case["spoken_text"])
        
        if not audio_content:
            logger.log_error("TTS conversion failed", "tts_error")
            logger.finalize_session(success=False)
            return False
        
        print(f"✅ Generated {len(audio_content)} bytes of audio")
        
        # Connect to WebSocket server
        live_api_endpoint = "ws://localhost:8765"
        print(f"🔌 Connecting to WebSocket at: {live_api_endpoint}")
        
        async with websockets.connect(live_api_endpoint) as websocket:
            # Send test initialization
            await websocket.send(json.dumps({
                "type": "start_test",
                "test_id": test_case['test_id']
            }))
            logger.log_server_response("start_test_sent", test_case['test_id'])
            
            # Start audio streaming
            chunk_size = 1024  # Send 1KB chunks
            total_chunks = (len(audio_content) + chunk_size - 1) // chunk_size
            print(f"📡 Streaming {len(audio_content)} bytes in {total_chunks} chunks...")
            
            # Stream audio data
            for i in range(0, len(audio_content), chunk_size):
                chunk = audio_content[i:i+chunk_size]
                audio_b64 = base64.b64encode(chunk).decode('utf-8')
                
                await websocket.send(json.dumps({
                    "type": "audio",
                    "data": audio_b64
                }))
                
                logger.log_audio_chunk(len(chunk))
                await asyncio.sleep(0.02)  # Simulate real-time streaming
            
            # Mark end of audio streaming
            session["audio_streaming_end_time"] = time.time()
            
            # Signal end of audio
            await websocket.send(json.dumps({"type": "end"}))
            logger.log_server_response("end_signal_sent", "audio_stream_complete")
            print("🏁 Finished streaming audio, waiting for response...")
            
            # Process server responses
            response_timeout = 30.0  # 30 second timeout
            start_wait_time = time.time()
            
            while True:
                try:
                    # Calculate remaining timeout
                    elapsed = time.time() - start_wait_time
                    remaining_timeout = max(0.1, response_timeout - elapsed)
                    
                    message = await asyncio.wait_for(websocket.recv(), timeout=remaining_timeout)
                    data = json.loads(message)
                    message_type = data.get("type")
                    
                    # Log all server responses
                    logger.log_server_response(message_type, data.get("data"))
                    
                    # Handle specific message types
                    if message_type == "itext":
                        # Input transcription (user speech)
                        text = data.get("data", "")
                        print(f"👤 User transcription: '{text}'")
                        logger.log_transcription("input", text)
                        
                    elif message_type == "otext":
                        # Output transcription (AI speech)
                        text = data.get("data", "")
                        print(f"🤖 AI transcription: '{text}'")
                        logger.log_transcription("output", text)
                        
                    elif message_type == "audio":
                        # Audio response from AI
                        session["audio_responses_received"] += 1
                        if session["audio_responses_received"] == 1:
                            print("🔊 First audio response received")
                        
                    elif message_type == "tool_call":
                        # Tool call detection (if server sends this info)
                        tool_data = data.get("data", {})
                        tool_name = tool_data.get("name", "unknown")
                        tool_args = tool_data.get("arguments")
                        print(f"🛠️ Tool call detected: {tool_name}")
                        logger.log_tool_call(tool_name, tool_args)
                        
                    elif message_type == "interrupted":
                        print("🤐 Response was interrupted")
                        logger.log_server_response("interrupted", data.get("data"))
                        
                    elif message_type == "error":
                        error_msg = data.get("data", "Unknown error")
                        print(f"❌ Server error: {error_msg}")
                        logger.log_error(error_msg, "server_error")
                        
                    elif message_type == "turn_complete" or message_type == "session_complete":
                        session["turn_complete_time"] = time.time()
                        print("✅ Turn completed by server")
                        logger.log_server_response("turn_complete", "session_ended")
                        break
                        
                    elif message_type == "ready":
                        print("✅ Server ready for next request")
                        break
                    
                except asyncio.TimeoutError:
                    print(f"⏰ Timeout waiting for server response ({response_timeout}s)")
                    logger.log_error(f"Response timeout after {response_timeout}s", "timeout")
                    break
                    
                except websockets.exceptions.ConnectionClosed:
                    print("🔌 Connection closed by server")
                    session["turn_complete_time"] = time.time()
                    break
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON from server: {e}")
                    logger.log_error(f"JSON decode error: {e}", "json_error")
                    continue
                    
                except Exception as e:
                    print(f"❌ Error processing server response: {e}")
                    logger.log_error(f"Response processing error: {e}", "processing_error")
                    break
        
        # Session completed successfully
        logger.finalize_session(success=True)
        return True
        
    except Exception as e:
        print(f"❌ Critical error in test case: {e}")
        logger.log_error(f"Critical error: {e}", "critical_error")
        logger.finalize_session(success=False)
        return False


async def run_test_cases(test_cases: List[Dict[str, Any]]):
    """
    Execute all test cases with comprehensive logging.
    """
    # Initialize logger
    logger = TestSessionLogger()
    
    # Clear previous logs
    if os.path.exists(logger.log_file):
        os.remove(logger.log_file)
        print(f"🗑️ Cleared previous log file: {logger.log_file}")
    
    successful_tests = 0
    total_tests = len(test_cases)
    
    print(f"\n🎯 Starting execution of {total_tests} test cases")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- Test Case {i}/{total_tests} ---")
        
        success = await run_single_test_case(test_case, logger)
        if success:
            successful_tests += 1
            print(f"✅ Test {i} completed successfully")
        else:
            print(f"❌ Test {i} failed")
        
        # Brief pause between tests
        if i < total_tests:
            print("⏸️ Pausing before next test...")
            await asyncio.sleep(2)
    
    # Final summary
    print("\n" + "=" * 60)
    print("🏁 Test Execution Complete")
    print(f"✅ Successful: {successful_tests}/{total_tests}")
    print(f"❌ Failed: {total_tests - successful_tests}/{total_tests}")
    print(f"📊 Success Rate: {(successful_tests/total_tests)*100:.1f}%")
    print(f"📝 Detailed logs saved to: {logger.log_file}")


def analyze_results_from_client_log(test_cases: List[Dict[str, Any]], log_file: str = "client_test_log.jsonl"):
    """
    Analyze test results using comprehensive client-side logs.
    
    This provides much more detailed analysis than server logs alone.
    """
    print("\n🔍 Analyzing Results from Client Logs")
    print("=" * 60)
    
    if not os.path.exists(log_file):
        print(f"❌ Error: Client log file not found at {log_file}")
        return
    
    # Load all session logs
    session_logs = []
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                session_logs.append(json.loads(line.strip()))
    except Exception as e:
        print(f"❌ Error reading log file: {e}")
        return
    
    # Create lookup by test_id
    sessions_by_id = {session['test_id']: session for session in session_logs}
    
    # Analysis metrics
    total_tests = len(test_cases)
    successful_tests = 0
    failed_tests = 0
    tool_call_accuracy = 0
    total_response_times = []
    total_ttft_times = []
    
    print(f"\n📋 Detailed Test Results:")
    print("-" * 60)
    
    for test_case in test_cases:
        test_id = test_case['test_id']
        expected_tool = test_case['expected_tool']
        
        print(f"\n🧪 Test {test_id}: {test_case['spoken_text']}")
        
        if test_id not in sessions_by_id:
            print("   ❌ FAILED: No session log found")
            failed_tests += 1
            continue
        
        session = sessions_by_id[test_id]
        
        # Check if session completed successfully
        if not session.get('session_completed', False):
            print("   ❌ FAILED: Session did not complete")
            failed_tests += 1
            continue
        
        # Analyze transcriptions
        input_text = session.get('complete_input_transcription', '')
        output_text = session.get('complete_output_transcription', '')
        
        print(f"   📝 Input transcription: '{input_text}'")
        print(f"   🤖 Output transcription: '{output_text}'")
        
        # Analyze tool calls
        tool_calls = session.get('tool_calls_detected', [])
        if tool_calls:
            for tool_call in tool_calls:
                print(f"   🛠️ Tool called: {tool_call['tool_name']}")
                if tool_call['tool_name'] == expected_tool:
                    tool_call_accuracy += 1
        else:
            print("   🚫 No tools called")
        
        # Timing analysis
        ttft = session.get('time_to_first_token')
        total_time = session.get('total_response_time')
        
        if ttft:
            print(f"   ⚡ Time to First Token: {ttft:.2f}ms")
            total_ttft_times.append(ttft)
        
        if total_time:
            print(f"   ⏱️ Total Response Time: {total_time:.2f}ms")
            total_response_times.append(total_time)
        
        # Error analysis
        errors = session.get('errors', [])
        if errors:
            print(f"   ⚠️ Errors encountered: {len(errors)}")
            for error in errors[:3]:  # Show first 3 errors
                print(f"      - {error['type']}: {error['message']}")
        
        # Final verdict for this test
        if session.get('success', False) and not errors:
            print("   ✅ PASSED")
            successful_tests += 1
        else:
            print("   ❌ FAILED")
            failed_tests += 1
    
    # Overall Statistics
    print("\n" + "=" * 60)
    print("📊 COMPREHENSIVE TEST ANALYSIS")
    print("=" * 60)
    print(f"📅 Analysis Date: {datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')}")
    print(f"📁 Log File: {log_file}")
    print(f"📋 Total Test Cases: {total_tests}")
    print(f"✅ Successful Tests: {successful_tests}")
    print(f"❌ Failed Tests: {failed_tests}")
    print(f"🎯 Success Rate: {(successful_tests/total_tests)*100:.1f}%")
    print(f"🛠️ Tool Call Accuracy: {(tool_call_accuracy/total_tests)*100:.1f}%")
    
    if total_ttft_times:
        avg_ttft = sum(total_ttft_times) / len(total_ttft_times)
        print(f"⚡ Average TTFT: {avg_ttft:.2f}ms")
        print(f"⚡ Min TTFT: {min(total_ttft_times):.2f}ms")
        print(f"⚡ Max TTFT: {max(total_ttft_times):.2f}ms")
    
    if total_response_times:
        avg_response = sum(total_response_times) / len(total_response_times)
        print(f"⏱️ Average Response Time: {avg_response:.2f}ms")
        print(f"⏱️ Min Response Time: {min(total_response_times):.2f}ms")
        print(f"⏱️ Max Response Time: {max(total_response_times):.2f}ms")
    
    print("=" * 60)


if __name__ == "__main__":
    # Load test cases
    script_dir = os.path.dirname(os.path.abspath(__file__))
    test_cases_path = os.path.join(script_dir, "test_cases.json")
    test_cases = load_test_cases_from_json(test_cases_path)
    
    if not test_cases:
        print("❌ No test cases to run. Exiting.")
        exit(1)
    
    # Execute test cases with comprehensive logging
    asyncio.run(run_test_cases(test_cases))
    
    # Analyze results using detailed client logs
    analyze_results_from_client_log(test_cases)