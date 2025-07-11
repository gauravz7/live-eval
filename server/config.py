# config.py - Central configuration for the API test framework
import os

# --- GCP Project & Model Details ---
PROJECT_ID = "cloud-llm-preview1"
LOCATION = "us-central1"
# The model used by your LiveAPI being tested
#LIVE_API_MODEL_NAME = 'gemini-live-2.5-flash'
LIVE_API_MODEL_NAME = 'gemini-live-2.5-flash-preview-native-audio'

# --- Text-to-Speech (TTS) Parameters for Chirp 3 ---
TTS_LOCATION = "global"
TTS_LANGUAGE_CODE = "en-US"
TTS_VOICE_NAME = "Puck"  # Example voice from Chirp 3 HD set
# CRITICAL: Gemini Live Audio Format Requirements
# Input to Gemini Live: 16-bit PCM, 16kHz, mono
TTS_AUDIO_ENCODING = "LINEAR16"  # 16-bit PCM
TTS_SAMPLE_RATE = 16000  # 16kHz - MUST match Gemini Live input requirement

# --- File & Directory Paths ---
# Use absolute paths to prevent issues when running scripts from different directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, "results")
# This is the path to the log file your server will write to.
# Ensure the server has write permissions to this location.
SERVER_LOG_FILE = os.path.join(BASE_DIR, "tool_call_log.jsonl")

# --- Live API Endpoint to Test ---
LIVE_API_ENDPOINT = "ws://localhost:8765"
