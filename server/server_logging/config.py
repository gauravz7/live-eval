# config.py - Central configuration for the API test framework
import os
import asyncio
import json
import base64
import logging
import websockets
import traceback
from websockets.exceptions import ConnectionClosed

# --- Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- GCP Project & Model Details ---
PROJECT_ID = "cloud-llm-preview1"
LOCATION = "us-central1"
#MODEL = 'gemini-live-2.5-flash-preview-native-audio'
#LIVE_API_MODEL_NAME = 'gemini-live-2.5-flash-preview-native-audio'

MODEL = 'gemini-live-2.5-flash'
LIVE_API_MODEL_NAME = 'gemini-live-2.5-flash'
VOICE_NAME = "Puck"

# --- Text-to-Speech (TTS) Parameters ---
TTS_LOCATION = "global"
TTS_LANGUAGE_CODE = "en-IN"
TTS_VOICE_NAME = "Puck"
TTS_AUDIO_ENCODING = "LINEAR16"
TTS_SAMPLE_RATE = 16000

# --- Audio Sample Rates ---
RECEIVE_SAMPLE_RATE = 24000
SEND_SAMPLE_RATE = 16000

# --- System Instruction ---
SYSTEM_INSTRUCTION = """
You are a helpful and knowledgeable assistant with access to a wide range of tools.

When a user asks a question, use the available tools to provide a comprehensive and accurate response. Your capabilities include:

Please use these tools to fulfill the user's requests.
"""

# --- File & Directory Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
SERVER_LOG_FILE = os.path.join(BASE_DIR, "tool_call_log.jsonl")

# --- Live API Endpoint to Test ---
LIVE_API_ENDPOINT = "ws://localhost:8765"

# --- Base WebSocket Server Class ---
class BaseWebSocketServer:
    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port
        self.active_clients = {}

    async def start(self):
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
        async with websockets.serve(self.handle_client, self.host, self.port):
            await asyncio.Future()

    async def handle_client(self, websocket):
        client_id = id(websocket)
        logger.info(f"New client connected: {client_id}")
        await websocket.send(json.dumps({"type": "ready"}))
        try:
            await self.process_audio(websocket, client_id)
        except ConnectionClosed:
            logger.info(f"Client disconnected: {client_id}")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
            logger.error(traceback.format_exc())
        finally:
            if client_id in self.active_clients:
                del self.active_clients[client_id]

    async def process_audio(self, websocket, client_id):
        raise NotImplementedError("Subclasses must implement process_audio")
