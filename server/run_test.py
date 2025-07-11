import asyncio
import json
import os
import time
from datetime import datetime
from typing import List, Dict, Any

import websockets
import base64
import importlib

import config
import tts_client
from google import genai

# Force reload of the config module to pick up changes
importlib.reload(config)

def load_test_cases_from_json(file_path: str) -> List[Dict[str, Any]]:
    """Loads test cases from a JSON file."""
    try:
        with open(file_path, 'r') as f:
            test_cases = json.load(f)
        print(f"✅ Successfully loaded {len(test_cases)} test cases from {file_path}")
        return test_cases
    except FileNotFoundError:
        print(f"❌ Error: Test case file not found at {file_path}")
        return []
    except json.JSONDecodeError:
        print(f"❌ Error: Could not decode JSON from {file_path}")
        return []


async def run_test_cases(test_cases: List[Dict[str, Any]]):
    """
    Executes the generated test cases against the LiveAPI server.
    """
    if os.path.exists(config.SERVER_LOG_FILE):
        os.remove(config.SERVER_LOG_FILE)

    for i, test_case in enumerate(test_cases):
        print(f"\n--- Running Test Case {i+1}/{len(test_cases)} ---")
        print(f"Spoken Text: {test_case['spoken_text']}")

        audio_content = tts_client.convert_text_to_audio(test_case["spoken_text"])

        if not audio_content:
            print("Skipping test case due to TTS failure.")
            continue

        try:
            live_api_endpoint = "ws://localhost:8765"
            print(f"Connecting to WebSocket at: {live_api_endpoint}")
            async with websockets.connect(live_api_endpoint) as websocket:
                # Stream the audio in chunks to simulate a real-time feed
                chunk_size = 1024  # Send 1KB chunks
                total_chunks = (len(audio_content) + chunk_size - 1) // chunk_size
                
                print(f"Streaming {len(audio_content)} bytes in {total_chunks} chunks...")

                for i in range(0, len(audio_content), chunk_size):
                    chunk = audio_content[i:i+chunk_size]
                    audio_b64 = base64.b64encode(chunk).decode('utf-8')
                    
                    await websocket.send(json.dumps({
                        "type": "audio",
                        "data": audio_b64
                    }))
                    
                    # Small delay to simulate real-time streaming
                    await asyncio.sleep(0.02) 

                print("Finished streaming audio.")
                # Signal that we are done sending audio
                await websocket.send(json.dumps({"type": "end"}))

                # Wait for the server to signal that the turn is complete
                print("Waiting for server to complete the turn...")
                while True:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        data = json.loads(message)
                        if data.get("type") == "turn_complete":
                            print("✅ Received turn_complete signal from server.")
                            break
                    except asyncio.TimeoutError:
                        print("⚠️ Timed out waiting for turn_complete signal.")
                        break
                    except websockets.exceptions.ConnectionClosed:
                        print("ℹ️ Connection closed by server.")
                        break
                    except Exception as e:
                        print(f"Error while waiting for server response: {e}")
                        break

        except Exception as e:
            print(f"Error connecting to or communicating with the server: {e}")

    print("\n--- Test Execution Finished ---")


def analyze_results(test_cases: List[Dict[str, Any]]):
    """
    Analyzes the results by comparing the expected tool calls with the actual
    tool calls logged by the server, providing a detailed report.
    """
    print("\n--- Analyzing Results ---")
    
    if not os.path.exists(config.SERVER_LOG_FILE):
        print("❌ Error: Log file not found. Cannot analyze results.")
        return

    with open(config.SERVER_LOG_FILE, 'r') as f:
        actual_calls = [json.loads(line) for line in f]

    passed_tests = 0
    failed_tests = 0
    
    print("\n--- Detailed Test Case Results ---")
    for i, expected in enumerate(test_cases):
        print(f"\n--- Test Case {i+1}: {expected['spoken_text']} ---")
        
        if i >= len(actual_calls):
            print("❌ FAILED: No tool call was logged for this test case.")
            failed_tests += 1
            continue

        actual = actual_calls[i]
        errors = []

        # 1. Check if a tool was called when one was expected
        if actual["tool_name"] == "NO_TOOL_CALLED":
            errors.append(f"Expected tool '{expected['expected_tool']}' to be called, but no tool was called.")
            if actual.get("model_response_transcription"):
                errors.append(f"  - Model response: '{actual['model_response_transcription']}'")
        else:
            # 2. Check if the correct tool was called
            if expected["expected_tool"] != actual["tool_name"]:
                errors.append(f"Expected tool '{expected['expected_tool']}', but got '{actual['tool_name']}'.")

        # 4. Report results
        if not errors:
            print(f"✅ PASSED: Correctly called '{actual['tool_name']}' in {actual['execution_time_ms']}ms.")
            passed_tests += 1
        else:
            print(f"❌ FAILED:")
            for error in errors:
                print(f"  - {error}")
            failed_tests += 1

    # --- Final Summary ---
    total_tests = len(test_cases)
    accuracy = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

    print("\n--- Test Run Complete ---")
    print(f"Date: {datetime.now().strftime('%A, %B %d, %Y at %I:%M %p')}")
    print("-----------------------------------------------------")
    print(f"Total Test Cases: {total_tests}")
    print(f"✅ Passed: {passed_tests}")
    print(f"❌ Failed: {failed_tests}")
    print(f"📈 Accuracy: {accuracy:.1f}%")
    print("-----------------------------------------------------")


if __name__ == "__main__":
    # Initialize the Gemini client (if needed for dynamic test case generation)
    # genai.configure(api_key="YOUR_API_KEY")

    # Step 1: Load Test Cases from JSON using a robust path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    test_cases_path = os.path.join(script_dir, "test_cases.json")
    test_cases = load_test_cases_from_json(test_cases_path)

    # Step 2: Test Execution
    asyncio.run(run_test_cases(test_cases))

    # The client now waits for turn_complete, so a final sleep is not necessary.
    # Step 3: Analysis and Reporting
    analyze_results(test_cases)
