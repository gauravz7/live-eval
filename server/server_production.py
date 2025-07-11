import asyncio
import json
import base64
import os
import time
import websockets
import logging
from google import genai
from google.genai import types
from google.genai.types import LiveConnectConfig, SpeechConfig, VoiceConfig, PrebuiltVoiceConfig
from common import BaseWebSocketServer, logger, PROJECT_ID, LOCATION, MODEL, SEND_SAMPLE_RATE, SYSTEM_INSTRUCTION
from tools import TOOLS_DEFINITION
import config

# Configure file logging for the production server
log_filename = "production.log"
if os.path.exists(log_filename):
    os.remove(log_filename) # Clear log on start
file_handler = logging.FileHandler(log_filename)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)

# Initialize Google client
client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

# Backend dummy functions
async def get_animal_info(animal_name: str):
    return {"result": f"Information about {animal_name}."}

async def get_planet_info(planet_name: str):
    return {"result": f"Information about {planet_name}."}

async def get_ocean_info(ocean_name: str):
    return {"result": f"Information about {ocean_name}."}

async def get_weather(location: str):
    return {"result": f"The weather in {location} is sunny."}

async def turn_on_lights(room: str):
    return {"result": f"Lights in {room} turned on successfully", "status": "on", "room": room}

async def turn_off_lights(room: str):
    return {"result": f"Lights in {room} turned off successfully", "status": "off", "room": room}

async def generate_report(topic: str):
    return {"result": f"A report on {topic} has been generated."}

async def generate_code(language: str, description: str):
    return {"result": f"Code in {language} for '{description}' has been generated."}

# Combined tools configuration
tools = [{"function_declarations": TOOLS_DEFINITION}]

# Load/Save session handle
def load_previous_session_handle():
    try:
        with open('session_handle.json', 'r') as f:
            return json.load(f).get('previous_session_handle')
    except FileNotFoundError:
        return None

def save_previous_session_handle(handle):
    with open('session_handle.json', 'w') as f:
        json.dump({'previous_session_handle': handle}, f)

CONFIG = {
    "response_modalities": ["AUDIO"], 
    "tools": tools,
    "system_instruction": SYSTEM_INSTRUCTION,
    "output_audio_transcription": {},
    "input_audio_transcription": {},
    "realtime_input_config": {
        "automatic_activity_detection": {"disabled": False}
    },
    "session_resumption": types.SessionResumptionConfig(handle=load_previous_session_handle()),
}

class LiveAPIWebSocketServer(BaseWebSocketServer):
    def __init__(self, host="0.0.0.0", port=8765):
        super().__init__(host, port)
        self.session = None

    async def safe_websocket_send(self, websocket, message):
        try:
            await websocket.send(json.dumps(message))
            return True
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed. Cannot send message.")
        except Exception as e:
            logger.warning(f"WebSocket send error: {e}")
        return False

    async def handle_tool_calls(self, response, websocket):
        if response.tool_call:
            function_responses = []
            for fc in response.tool_call.function_calls:
                if fc.name == "get_animal_info":
                    response_data = await get_animal_info(fc.args.get("animal_name"))
                elif fc.name == "get_planet_info":
                    response_data = await get_planet_info(fc.args.get("planet_name"))
                elif fc.name == "get_ocean_info":
                    response_data = await get_ocean_info(fc.args.get("ocean_name"))
                elif fc.name == "get_weather":
                    response_data = await get_weather(fc.args.get("location"))
                elif fc.name == "turn_on_lights":
                    response_data = await turn_on_lights(fc.args.get("room"))
                elif fc.name == "turn_off_lights":
                    response_data = await turn_off_lights(fc.args.get("room"))
                elif fc.name == "generate_report":
                    response_data = await generate_report(fc.args.get("topic"))
                elif fc.name == "generate_code":
                    response_data = await generate_code(fc.args.get("language"), fc.args.get("description"))
                else:
                    response_data = {"result": "Unknown function"}
                
                function_responses.append(types.FunctionResponse(id=fc.id, name=fc.name, response=response_data))
            
            await self.session.send_tool_response(function_responses=function_responses)

    async def process_audio(self, websocket, client_id):
        try:
            async with client.aio.live.connect(model=MODEL, config=CONFIG) as session:
                self.session = session
                
                async with asyncio.TaskGroup() as tg:
                    async def handle_websocket_messages():
                        async for message in websocket:
                            data = json.loads(message)
                            if data.get("type") == "audio":
                                audio_bytes = base64.b64decode(data.get("data", ""))
                                await session.send_realtime_input(audio=types.Blob(data=audio_bytes, mime_type=f"audio/pcm;rate={SEND_SAMPLE_RATE}"))
                    
                    async def receive_and_play():
                        while True:
                            async for response in session.receive():
                                await self.handle_tool_calls(response, websocket)
                                if response.session_resumption_update and response.session_resumption_update.new_handle:
                                    save_previous_session_handle(response.session_resumption_update.new_handle)
                                    await self.safe_websocket_send(websocket, {"type": "session_id", "data": response.session_resumption_update.new_handle})
                                
                                if data := response.data:
                                    await self.safe_websocket_send(websocket, {"type": "audio", "data": base64.b64encode(data).decode('utf-8')})
                                
                                if response.server_content:
                                    if response.server_content.output_transcription:
                                        await self.safe_websocket_send(websocket, {"type": "otext", "data": response.server_content.output_transcription.text})
                                    if response.server_content.input_transcription:
                                        await self.safe_websocket_send(websocket, {"type": "itext", "data": response.server_content.input_transcription.text})
                                    if response.server_content.turn_complete:
                                        await self.safe_websocket_send(websocket, {"type": "turn_complete"})

                    tg.create_task(handle_websocket_messages())
                    tg.create_task(receive_and_play())

        except Exception as e:
            logger.error(f"Critical error in process_audio: {e}")
            await self.safe_websocket_send(websocket, {"type": "error", "data": str(e)})

async def main():
    server = LiveAPIWebSocketServer()
    await server.start()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Exiting application.")
