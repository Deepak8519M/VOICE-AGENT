import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
import re

import assemblyai as aai
from fastapi import FastAPI, WebSocket, Request, Query, WebSocketException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from google.generativeai import GenerativeModel, configure
import websockets
from dotenv import load_dotenv
import aiohttp
import PyPDF2

# Load environment variables
load_dotenv()

# Logging configuration
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
log = logging.getLogger("novaflow")

# FastAPI app
app = FastAPI(title="NovaFlow AI Voice Agent")

# Store the main event loop
main_loop = asyncio.get_event_loop()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Directories
UPLOAD_DIR = "uploads"
KNOWLEDGE_BASE_DIR = os.path.join(UPLOAD_DIR, "knowledge_base")
CHAT_DIR = os.path.join(UPLOAD_DIR, "chats")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(KNOWLEDGE_BASE_DIR, exist_ok=True)
os.makedirs(CHAT_DIR, exist_ok=True)

# Audio configuration
SAMPLE_RATE = 44100  # Match index.js
MIN_AUDIO_DURATION_MS = 1000  # Require 1 second of audio
MIN_BUFFER_SIZE = int(SAMPLE_RATE * MIN_AUDIO_DURATION_MS / 1000 * 2)  # 88200 bytes

# In-memory storage for user settings
USER_API_KEYS: Dict[str, str] = {}
USER_OVERRIDE_ENV: bool = False
USER_SETTINGS: Dict[str, Any] = {
    "voiceId": "en-IN-alia",
    "playbackSpeed": 1.0,
    "conversationType": "casual",
    "micSensitivity": 50,
    "audioQuality": "medium",
    "autoSaveHistory": True,
    "includeKnowledgeBase": True,
    "enableSearch": True,
    "maxSearchResults": 3,
    "enableSound": True,
    "notificationDuration": 4,
    "theme": "dark",
    "accentColor": "orange"
}

# Knowledge base storage
KNOWLEDGE_BASE: Dict[str, str] = {}

# Constants
CONTEXT_ID = "storyteller_context_27"
MURF_WS_URL_DEFAULT = "wss://api.murf.ai/v1/speech/stream-input"

# Utility Functions
def get_chat_file(chat_id: str) -> str:
    return os.path.join(CHAT_DIR, f"{chat_id}.json")

def sanitize_filename(filename: str) -> str:
    return re.sub(r'[^\w\s.-]', '', filename)

def save_chat_history(chat_id: str, user_query: str, ai_response: str) -> bool:
    if not USER_SETTINGS.get("autoSaveHistory", True):
        log.info(f"Chat history saving disabled for {chat_id}")
        return False
    try:
        file = get_chat_file(chat_id)
        history = []
        if os.path.exists(file):
            with open(file, "r") as f:
                history = json.load(f)
        entry = {
            "timestamp": datetime.now().isoformat(),
            "user_query": user_query,
            "ai_response": ai_response,
        }
        history.append(entry)
        with open(file, "w") as f:
            json.dump(history, f, indent=2)
        log.info(f"Chat history saved for {chat_id}: {entry}")
        return True
    except Exception as e:
        log.error(f"Failed to save chat history for {chat_id}: {e}")
        return False

def get_api_key(key_name: str, websocket: Optional[WebSocket] = None) -> str:
    env_key = os.getenv(key_name, "")
    user_key = USER_API_KEYS.get(key_name, "")
    if USER_OVERRIDE_ENV and user_key:
        log.info(f"Using user-provided {key_name} from USER_API_KEYS")
        return user_key
    elif env_key:
        log.info(f"Using {key_name} from .env file")
        return env_key
    elif user_key:
        log.warning(f"No {key_name} in .env; falling back to user-provided key")
        return user_key
    else:
        error_msg = f"No {key_name} found in .env or user-provided keys"
        log.error(error_msg)
        if websocket:
            asyncio.create_task(websocket.send_json({
                "type": "error",
                "data": error_msg
            }))
        return ""

# Routes
@app.get("/")
async def home(request: Request):
    log.info("Serving home page")
    return templates.TemplateResponse("home.html", {"request": request})

@app.get("/app")
async def app_page(request: Request):
    log.info("Serving app page")
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/docu")
async def docs(request: Request):
    log.info("Serving docs page")
    return templates.TemplateResponse("docs.html", {"request": request})

@app.get("/settings")
async def settings(request: Request):
    log.info("Serving settings page")
    return templates.TemplateResponse("settings.html", {"request": request})

@app.get("/chats")
async def list_chats():
    try:
        chats = [f.split('.')[0] for f in os.listdir(CHAT_DIR) if f.endswith('.json')]
        return sorted(chats, key=lambda x: int(x) if x.isdigit() else 0)
    except Exception as e:
        log.error(f"Failed to list chats: {e}")
        return []

@app.post("/new_chat")
async def new_chat():
    try:
        chats = await list_chats()
        new_id = str(max([int(c) for c in chats if c.isdigit()] or [0]) + 1)
        file = get_chat_file(new_id)
        with open(file, "w") as f:
            json.dump([], f)
        log.info(f"Created new chat: {new_id}")
        return {"chat_id": new_id}
    except Exception as e:
        log.error(f"Failed to create new chat: {e}")
        return {"error": str(e)}

@app.get("/chat_history")
async def get_chat_history(chat_id: str = Query("1")):
    try:
        file = get_chat_file(chat_id)
        if os.path.exists(file):
            with open(file, "r") as f:
                return json.load(f)
        return []
    except Exception as e:
        log.error(f"Failed to read chat history for {chat_id}: {e}")
        return {"error": str(e)}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        sanitized_filename = sanitize_filename(file.filename)
        file_path = os.path.join(KNOWLEDGE_BASE_DIR, sanitized_filename)
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        extracted_text = ""
        if sanitized_filename.endswith(".pdf"):
            try:
                with open(file_path, "rb") as f:
                    pdf = PyPDF2.PdfReader(f)
                    extracted_text = "\n".join(page.extract_text() or "" for page in pdf.pages)
                if not extracted_text.strip():
                    log.warning(f"No text extracted from PDF: {sanitized_filename}")
                    return {
                        "message": f"File {sanitized_filename} uploaded, but no text could be extracted.",
                        "extracted_text": ""
                    }
            except Exception as e:
                log.error(f"Failed to process PDF {sanitized_filename}: {e}")
                return {
                    "message": f"File {sanitized_filename} uploaded, but an error occurred: {str(e)}",
                    "extracted_text": ""
                }
        elif sanitized_filename.endswith(".txt"):
            with open(file_path, "r", encoding="utf-8") as f:
                extracted_text = f.read()
        else:
            return {
                "message": f"File {sanitized_filename} uploaded, but only .pdf and .txt are supported.",
                "extracted_text": ""
            }
        content_file = os.path.join(KNOWLEDGE_BASE_DIR, f"{sanitized_filename}.txt")
        with open(content_file, "w", encoding="utf-8") as f:
            f.write(extracted_text)
        KNOWLEDGE_BASE[sanitized_filename] = extracted_text
        word_count = len(extracted_text.split())
        log.info(f"Processed file {sanitized_filename}: {word_count} words extracted")
        text_preview = extracted_text[:200] + ("..." if len(extracted_text) > 200 else "")
        return {
            "message": f"File {sanitized_filename} uploaded and processed successfully! Extracted {word_count} words.",
            "extracted_text": text_preview
        }
    except Exception as e:
        log.error(f"Failed to upload file {file.filename}: {e}")
        return {
            "message": f"Failed to upload file {file.filename}: {str(e)}",
            "extracted_text": ""
        }

@app.post("/set_keys")
async def set_api_keys(keys: Dict[str, str]):
    global USER_API_KEYS, USER_OVERRIDE_ENV
    try:
        required_keys = ["aai_api_key", "gemini_api_key", "murf_api_key", "tavily_api_key"]
        USER_OVERRIDE_ENV = keys.get("override_env", "false").lower() == "true"
        USER_API_KEYS.update({k: v for k, v in keys.items() if k in required_keys or k == "zapier_webhook_url"})
        log.info("API keys updated successfully")
        return {"message": "API keys saved successfully."}
    except Exception as e:
        error_msg = f"Failed to set API keys: {str(e)}. Falling back to .env keys."
        log.error(error_msg)
        USER_API_KEYS.update({k: v for k, v in keys.items() if k in required_keys or k == "zapier_webhook_url"})
        return {"error": error_msg}

@app.post("/set_settings")
async def set_settings(settings: Dict[str, Any]):
    global USER_SETTINGS
    try:
        USER_SETTINGS.update(settings)
        with open("settings.json", "w") as f:
            json.dump(USER_SETTINGS, f, indent=2)
        log.info("Settings updated successfully")
        return {"message": "Settings saved successfully."}
    except Exception as e:
        log.error(f"Failed to set settings: {e}")
        return {"error": str(e)}

@app.get("/get_settings")
async def get_settings():
    try:
        return USER_SETTINGS
    except Exception as e:
        log.error(f"Failed to get settings: {e}")
        return {"error": str(e)}

@app.post("/reset_settings")
async def reset_settings(data: Dict[str, bool]):
    global USER_API_KEYS, USER_OVERRIDE_ENV, USER_SETTINGS
    try:
        if data.get("reset"):
            USER_API_KEYS = {}
            USER_OVERRIDE_ENV = False
            USER_SETTINGS = {
                "voiceId": "en-IN-alia",
                "playbackSpeed": 1.0,
                "conversationType": "casual",
                "micSensitivity": 50,
                "audioQuality": "medium",
                "autoSaveHistory": True,
                "includeKnowledgeBase": True,
                "enableSearch": True,
                "maxSearchResults": 3,
                "enableSound": True,
                "notificationDuration": 4,
                "theme": "dark",
                "accentColor": "orange"
            }
            with open("settings.json", "w") as f:
                json.dump(USER_SETTINGS, f, indent=2)
            log.info("Settings reset to defaults")
            return {"message": "Settings reset successfully."}
        return {"error": "Invalid reset request"}
    except Exception as e:
        log.error(f"Failed to reset settings: {e}")
        return {"error": str(e)}

@app.post("/clear_chat_history")
async def clear_chat_history(data: Dict[str, bool]):
    try:
        if data.get("clear"):
            for file in os.listdir(CHAT_DIR):
                os.remove(os.path.join(CHAT_DIR, file))
            log.info("Chat history cleared")
            return {"message": "Chat history cleared successfully."}
        return {"error": "Invalid clear request"}
    except Exception as e:
        log.error(f"Failed to clear chat history: {e}")
        return {"error": str(e)}

@app.post("/clear_knowledge_base")
async def clear_knowledge_base(data: Dict[str, bool]):
    global KNOWLEDGE_BASE
    try:
        if data.get("clear"):
            for file in os.listdir(KNOWLEDGE_BASE_DIR):
                os.remove(os.path.join(KNOWLEDGE_BASE_DIR, file))
            KNOWLEDGE_BASE = {}
            log.info("Knowledge base cleared")
            return {"message": "Knowledge base cleared successfully."}
        return {"error": "Invalid clear request"}
    except Exception as e:
        log.error(f"Failed to clear knowledge base: {e}")
        return {"error": str(e)}

async def tavily_search(query: str, websocket: WebSocket) -> str:
    if not USER_SETTINGS.get("enableSearch", True):
        return "Search is disabled in settings."
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://api.tavily.com/search",
            json={"api_key": get_api_key("tavily_api_key", websocket), "query": query, "max_results": USER_SETTINGS.get("maxSearchResults", 3)},
        ) as response:
            if response.status == 200:
                data = await response.json()
                results = data.get("results", [])
                if not results:
                    return "No search results found."
                summary = "Here are the top search results:\n"
                for idx, result in enumerate(results, 1):
                    summary += f"{idx}. {result['title']}: {result['content'][:200]}... (Source: {result['url']})\n"
                return summary
            else:
                error_msg = f"Error: Unable to perform web search (status {response.status})."
                await websocket.send_json({"type": "error", "data": error_msg})
                return error_msg

async def stream_gemini_response(chat_id: str, transcript: str, websocket: WebSocket, is_voice_input: bool = False) -> Optional[str]:
    try:
        if not isinstance(transcript, str) or not transcript.strip():
            log.error(f"Invalid transcript: {transcript}")
            await websocket.send_json({"type": "error", "data": "Invalid query provided"})
            return None

        await websocket.send_json({
            "type": "user_message",
            "data": transcript,
            "is_final": True
        })

        gemini_api_key = get_api_key("gemini_api_key", websocket)
        if not gemini_api_key:
            error_msg = "No valid Gemini API key found"
            log.error(error_msg)
            await websocket.send_json({"type": "error", "data": error_msg})
            return None
        configure(api_key=gemini_api_key)

        original_transcript = transcript
        if USER_SETTINGS.get("includeKnowledgeBase", True) and "summary" in transcript.lower():
            query_words = set(re.sub(r'[^\w\s]', '', transcript.lower()).split())
            for filename in KNOWLEDGE_BASE:
                filename_words = set(re.sub(r'[^\w\s]', '', filename.lower()).split())
                if query_words & filename_words:
                    transcript = f"Summarize the content of the file '{filename}'"
                    log.info(f"Rewrote query '{original_transcript}' to '{transcript}'")
                    break

        if USER_SETTINGS.get("enableSearch", True) and any(word in transcript.lower() for word in ["search", "find", "look up"]):
            log.info(f"Performing search for: {transcript}")
            accumulated_response = await tavily_search(transcript, websocket)
            if is_voice_input:
                murf_ws_url = f"{MURF_WS_URL_DEFAULT}?api_key={get_api_key('murf_api_key', websocket)}&context_id={CONTEXT_ID}&format=WAV&sample_rate=44100&channel_type=MONO"
                async with websockets.connect(murf_ws_url, ping_interval=None) as murf_ws:
                    await murf_ws.send(json.dumps({"init": True}))
                    voice_config = {"voice_config": {"voiceId": USER_SETTINGS.get("voiceId", "en-IN-alia"), "style": "Narration", "speed": USER_SETTINGS.get("playbackSpeed", 1.0)}}
                    await murf_ws.send(json.dumps(voice_config))
                    await murf_ws.send(json.dumps({"text": accumulated_response}))
                    murf_response = await asyncio.wait_for(murf_ws.recv(), timeout=10.0)
                    murf_data = json.loads(murf_response)
                    base64_audio = murf_data.get("audio", "")
                    is_final = murf_data.get("is_final", False)
                    if base64_audio:
                        await websocket.send_json({
                            "type": "audio",
                            "data": base64_audio,
                            "is_final": is_final
                        })
                        log.info(f"Sent search audio to client (Final: {is_final}, Length: {len(base64_audio)})")
                    while not is_final:
                        try:
                            murf_response = await asyncio.wait_for(murf_ws.recv(), timeout=5.0)
                            murf_data = json.loads(murf_response)
                            base64_audio = murf_data.get("audio", "")
                            is_final = murf_data.get("is_final", False)
                            if base64_audio:
                                await websocket.send_json({
                                    "type": "audio",
                                    "data": base64_audio,
                                    "is_final": is_final
                                })
                                log.info(f"Sent additional base64 audio to client (Final: {is_final}, Length: {len(base64_audio)})")
                        except asyncio.TimeoutError:
                            log.warning("Timeout waiting for additional Murf audio")
                            break
            if accumulated_response:
                save_chat_history(chat_id, original_transcript, accumulated_response)
                await websocket.send_json({
                    "type": "search",
                    "data": accumulated_response
                })
            if "send to email" in original_transcript.lower() or "email the summary" in original_transcript.lower():
                async with aiohttp.ClientSession() as session:
                    async with session.post(get_api_key("zapier_webhook_url", websocket), json={"response": accumulated_response}) as resp:
                        log.info(f"Sent search response to Zapier webhook: {resp.status}")
                        await websocket.send_json({
                            "type": "zapier",
                            "data": "Email sent successfully"
                        })
            return accumulated_response

        log.debug(f"Calling Gemini with transcript: {transcript}")
        conversation_type = USER_SETTINGS.get("conversationType", "casual")
        system_instruction = {
            "casual": "You are a friendly and approachable assistant. Use simple, conversational language with a relaxed tone.",
            "formal": "You are a professional assistant. Use clear, polite, and formal language in your responses.",
            "technical": "You are a technical expert. Provide detailed, precise, and technical responses suitable for advanced users."
        }.get(conversation_type, "You are a wise and gentle guide. Your tone is calm, clear, and comforting, like a thoughtful elder or a trusted friend. "
                              "You explain things in a simple way, sometimes using small analogies or everyday examples if they help. "
                              "Keep responses natural and conversational — never too formal, never dramatic, and not motivational. "
                              "The goal is to make the user feel relaxed, understood, and stress-free, while still giving useful and thoughtful answers.")

        model = GenerativeModel(
            model_name="gemini-1.5-flash",
            system_instruction=system_instruction
        )
        contents = [{"role": "user", "parts": [{"text": transcript}]}]
        if USER_SETTINGS.get("includeKnowledgeBase", True) and KNOWLEDGE_BASE:
            knowledge_context = "\n\nKnowledge Base Content:\n"
            for filename, content in KNOWLEDGE_BASE.items():
                knowledge_context += f"\nFile: {filename}\n{content[:2000]}...\n"
            contents[0]["parts"].append({"text": knowledge_context})

        response = model.generate_content(contents, stream=False)
        accumulated_response = response.text

        if is_voice_input:
            murf_ws_url = f"{MURF_WS_URL_DEFAULT}?api_key={get_api_key('murf_api_key', websocket)}&context_id={CONTEXT_ID}&format=WAV&sample_rate=44100&channel_type=MONO"
            async with websockets.connect(murf_ws_url, ping_interval=None) as murf_ws:
                await murf_ws.send(json.dumps({"init": True}))
                voice_config = {"voice_config": {"voiceId": USER_SETTINGS.get("voiceId", "en-IN-alia"), "style": "Narration", "speed": USER_SETTINGS.get("playbackSpeed", 1.0)}}
                await murf_ws.send(json.dumps(voice_config))
                await murf_ws.send(json.dumps({"text": accumulated_response}))
                murf_response = await asyncio.wait_for(murf_ws.recv(), timeout=10.0)
                murf_data = json.loads(murf_response)
                base64_audio = murf_data.get("audio", "")
                is_final = murf_data.get("is_final", False)
                if base64_audio:
                    await websocket.send_json({
                        "type": "audio",
                        "data": base64_audio,
                        "is_final": is_final
                    })
                    log.info(f"Sent base64 audio to client (Final: {is_final}, Length: {len(base64_audio)})")
                while not is_final:
                    try:
                        murf_response = await asyncio.wait_for(murf_ws.recv(), timeout=5.0)
                        murf_data = json.loads(murf_response)
                        base64_audio = murf_data.get("audio", "")
                        is_final = murf_data.get("is_final", False)
                        if base64_audio:
                            await websocket.send_json({
                                "type": "audio",
                                "data": base64_audio,
                                "is_final": is_final
                            })
                            log.info(f"Sent additional base64 audio to client (Final: {is_final}, Length: {len(base64_audio)})")
                    except asyncio.TimeoutError:
                        log.warning("Timeout waiting for additional Murf audio")
                        break

        if accumulated_response:
            save_chat_history(chat_id, original_transcript, accumulated_response)
            await websocket.send_json({
                "type": "response",
                "data": accumulated_response
            })
            if "send to email" in original_transcript.lower() or "email the summary" in original_transcript.lower():
                async with aiohttp.ClientSession() as session:
                    async with session.post(get_api_key("zapier_webhook_url", websocket), json={"response": accumulated_response}) as resp:
                        log.info(f"Sent response to Zapier webhook: {resp.status}")
                        await websocket.send_json({
                            "type": "zapier",
                            "data": "Email sent successfully"
                        })
        log.info("Gemini Response Complete.")
        return accumulated_response
    except Exception as e:
        log.error(f"Error in stream_gemini_response: {e}")
        await websocket.send_json({"type": "error", "data": f"Error processing response: {str(e)}"})
        return None

@app.websocket("/ws")
async def ws_handler(websocket: WebSocket, chat_id: str = Query(...)):
    if not chat_id:
        raise WebSocketException(code=400, reason="Missing chat_id")
    file = get_chat_file(chat_id)
    if not os.path.exists(file):
        raise WebSocketException(code=403, reason="Chat ID does not exist")
    await websocket.accept()
    log.info(f"WebSocket connected for chat_id: {chat_id}")

    transcriber = None
    try:
        # Configure AssemblyAI RealtimeTranscriber
        aai.settings.api_key = get_api_key("aai_api_key", websocket)
        transcriber = aai.RealtimeTranscriber(
            sample_rate=SAMPLE_RATE,
            on_data=lambda transcript: asyncio.run_coroutine_threadsafe(
                forward_event(transcript, websocket, chat_id), main_loop
            ),
            on_error=lambda error: asyncio.run_coroutine_threadsafe(
                forward_event(error, websocket, chat_id), main_loop
            ),
        )

        all_transcripts = []
        final_transcript = None
        start_time = None

        async def forward_event(message, websocket, chat_id):
            nonlocal final_transcript
            try:
                if isinstance(message, aai.RealtimeError):
                    error_msg = f"Streaming error: {str(message)}"
                    log.error(error_msg)
                    await websocket.send_json({"type": "error", "data": error_msg})
                elif isinstance(message, aai.RealtimeTranscript):
                    transcript_text = message.text.strip()
                    if transcript_text:
                        all_transcripts.append(transcript_text)
                        log.info(f"Live Transcription: {transcript_text}")
                        await websocket.send_json({
                            "type": "user_message",
                            "data": transcript_text,
                            "is_final": message.is_final
                        })
                        if message.is_final:
                            final_transcript = transcript_text
                            log.info(f"Final Transcription: {final_transcript}")
                            await websocket.send_json({"type": "turn_ended"})
                            await stream_gemini_response(chat_id, final_transcript, websocket, is_voice_input=True)
                else:
                    log.warning(f"Received unknown message type: {type(message)}")
            except Exception as e:
                log.error(f"forward_event error: {e}")
                await websocket.send_json({"type": "error", "data": f"Transcription error: {str(e)}"})

        transcriber.connect()

        audio_buffer = bytearray()
        last_send_time = datetime.now()

        while True:
            msg = await websocket.receive()
            if msg["type"] == "websocket.disconnect":
                break
            elif msg["type"] == "websocket.receive":
                data = msg.get("bytes") or msg.get("text")
                if isinstance(data, str):
                    if data == "start":
                        start_time = datetime.now()
                        await websocket.send_text("Started transcription")
                        if USER_SETTINGS.get("enableSound", True):
                            await websocket.send_json({"type": "sound_alert", "data": "start"})
                    elif data == "stop":
                        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000 if start_time else 0
                        if elapsed_ms < MIN_AUDIO_DURATION_MS:
                            log.warning(f"Recording too short: {elapsed_ms:.1f}ms, required: {MIN_AUDIO_DURATION_MS}ms")
                            await websocket.send_json({
                                "type": "error",
                                "data": f"Recording too short ({elapsed_ms:.1f}ms). Please speak for at least 1 second."
                            })
                        elif audio_buffer and len(audio_buffer) >= MIN_BUFFER_SIZE:
                            transcriber.stream(audio_buffer)
                            log.debug(f"Sent final audio chunk: {len(audio_buffer)} bytes")
                        else:
                            log.warning(f"Audio buffer too small: {len(audio_buffer)} bytes, required: {MIN_BUFFER_SIZE} bytes")
                            await websocket.send_json({
                                "type": "error",
                                "data": f"Insufficient audio data ({len(audio_buffer)} bytes). Please speak for at least 1 second."
                            })
                        transcriber.close()
                        await websocket.send_text("Stopped transcription")
                        if USER_SETTINGS.get("enableSound", True):
                            await websocket.send_json({"type": "sound_alert", "data": "stop"})
                    elif data.startswith("text:"):
                        transcript = data[5:].strip()
                        if transcript:
                            await stream_gemini_response(chat_id, transcript, websocket, is_voice_input=False)
                    elif data.startswith("speak:"):
                        transcript = data[6:].strip()
                        if transcript:
                            murf_ws_url = f"{MURF_WS_URL_DEFAULT}?api_key={get_api_key('murf_api_key', websocket)}&context_id={CONTEXT_ID}&format=WAV&sample_rate=44100&channel_type=MONO"
                            async with websockets.connect(murf_ws_url, ping_interval=None) as murf_ws:
                                await murf_ws.send(json.dumps({"init": True}))
                                voice_config = {"voice_config": {"voiceId": USER_SETTINGS.get("voiceId", "en-IN-alia"), "style": "Narration", "speed": USER_SETTINGS.get("playbackSpeed", 1.0)}}
                                await murf_ws.send(json.dumps(voice_config))
                                await murf_ws.send(json.dumps({"text": transcript}))
                                murf_response = await asyncio.wait_for(murf_ws.recv(), timeout=10.0)
                                murf_data = json.loads(murf_response)
                                base64_audio = murf_data.get("audio", "")
                                is_final = murf_data.get("is_final", False)
                                if base64_audio:
                                    await websocket.send_json({
                                        "type": "speak_audio",
                                        "data": base64_audio,
                                        "is_final": is_final
                                    })
                                while not is_final:
                                    try:
                                        murf_response = await asyncio.wait_for(murf_ws.recv(), timeout=5.0)
                                        murf_data = json.loads(murf_response)
                                        base64_audio = murf_data.get("audio", "")
                                        is_final = murf_data.get("is_final", False)
                                        if base64_audio:
                                            await websocket.send_json({
                                                "type": "speak_audio",
                                                "data": base64_audio,
                                                "is_final": is_final
                                            })
                                    except asyncio.TimeoutError:
                                        break
                elif isinstance(data, bytes):
                    audio_buffer.extend(data)
                    current_time = datetime.now()
                    elapsed_ms = (current_time - last_send_time).total_seconds() * 1000
                    if elapsed_ms >= 100 and len(audio_buffer) >= MIN_BUFFER_SIZE:
                        try:
                            transcriber.stream(audio_buffer)
                            log.debug(f"Sent audio chunk: {len(audio_buffer)} bytes, {elapsed_ms:.1f} ms")
                            audio_buffer = bytearray()
                            last_send_time = current_time
                        except Exception as e:
                            log.error(f"Error streaming audio to AssemblyAI: {e}")
                            await websocket.send_json({"type": "error", "data": f"Audio streaming error: {str(e)}"})
                            transcriber.close()
                            break
                else:
                    log.warning(f"Received invalid data type: {type(data)}")
                    await websocket.send_json({"type": "error", "data": "Invalid data received"})
    except Exception as e:
        log.error(f"WebSocket error: {e}")
        await websocket.send_json({"type": "error", "data": f"WebSocket error: {str(e)}"})
    finally:
        if transcriber:
            transcriber.close()
        await websocket.close()
        log.info("WebSocket closed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)