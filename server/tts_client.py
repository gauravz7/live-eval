# tts_client.py - A dedicated client for Google Cloud Text-to-Speech
import config
from google.api_core.client_options import ClientOptions
from google.cloud import texttospeech_v1beta1 as texttospeech

def convert_text_to_audio(text: str) -> bytes:
    """Synthesizes speech from text using Google Cloud's TTS API."""
    try:
        # Construct the correct API endpoint based on the location
        api_endpoint = (
            f"{config.TTS_LOCATION}-texttospeech.googleapis.com"
            if config.TTS_LOCATION != "global"
            else "texttospeech.googleapis.com"
        )
        client = texttospeech.TextToSpeechClient(
            client_options=ClientOptions(api_endpoint=api_endpoint)
        )

        # Construct the full voice name from the config
        full_voice_name = f"{config.TTS_LANGUAGE_CODE}-Chirp3-HD-{config.TTS_VOICE_NAME}"

        # Set up the synthesis request
        synthesis_input = texttospeech.SynthesisInput(text=text)
        voice_params = texttospeech.VoiceSelectionParams(
            name=full_voice_name, language_code=config.TTS_LANGUAGE_CODE
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding[config.TTS_AUDIO_ENCODING],
            sample_rate_hertz=config.TTS_SAMPLE_RATE
        )

        # Make the API call
        print(f"🔊 Generating audio for: '{text[:40]}...'")
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice_params, audio_config=audio_config
        )
        
        # --- START: Audio Padding ---
        # Generate 3 seconds of silence by creating raw silent audio data.
        # 16kHz, 16-bit mono audio means 16000 * 2 = 32000 bytes per second.
        # 3 seconds of silence = 32000 * 3 = 96000 bytes of zeros.
        silent_audio = b'\x00' * 32000
        
        print(f"Adding 1s of silence padding at the beginning and end.")
        
        # Combine the audio parts
        padded_audio = silent_audio + response.audio_content + silent_audio
        
        return padded_audio
        # --- END: Audio Padding ---

    except Exception as e:
        print(f"❌ TTS Client Error: {e}")
        return None
