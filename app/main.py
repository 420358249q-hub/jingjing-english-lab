"""
WaXueShe Mini - Main Application Entrypoint
FastAPI backend powering Daily Conversation, Sentence Building, and AI Speech
"""

import os
import datetime
from fastapi import FastAPI, HTTPException, Response, UploadFile, File, BackgroundTasks
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import tempfile

from app.data_bank import SCENARIOS, SENTENCE_DRILLS
from app.custom_manager import (
    load_custom_drills,
    save_custom_drills,
    delete_single_custom_drill,
    delete_all_custom_drills,
    generate_drills_from_text
)
from app.ollama_client import (
    get_installed_models,
    select_best_model,
    chat_with_ollama,
    stream_chat_with_ollama,
    evaluate_with_ollama
)
from app.tts_engine import (
    check_kokoro_status,
    synthesize_speech
)

app = FastAPI(title="静静学习系统 - AI 英语私教研习室")

@app.on_event("startup")
async def startup_warmup():
    import asyncio
    async def _do_warmup():
        try:
            # Pre-warm first sentence drill so 1st click has 0ms latency
            await synthesize_speech("There are three red apples and two bananas on the table.", voice="af_heart")
            print("[TTS Engine] Initial sentence pre-warmed into disk cache.")
        except Exception as e:
            print(f"[TTS Warmup Warning] {e}")
    asyncio.create_task(_do_warmup())

# Whisper model cache
_whisper_model = None

def get_whisper():
    global _whisper_model
    if _whisper_model is not None:
        return _whisper_model
    try:
        from faster_whisper import WhisperModel
        # Using tiny.en (only 75MB, transcribes in 100ms on Apple Silicon)
        _whisper_model = WhisperModel("tiny.en", device="cpu", compute_type="int8")
        return _whisper_model
    except Exception as e:
        print(f"[Whisper Init Error] {e}")
        return None

# CORS middleware for development flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Request Models -----------------

class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    scenario: Optional[str] = "freetalk"
    model: Optional[str] = None

class EvaluateRequest(BaseModel):
    conversation: List[Dict[str, str]]
    model: Optional[str] = None

class TTSRequest(BaseModel):
    text: str
    engine: Optional[str] = "kokoro"   # Default to Kokoro-82M v1.0
    voice: Optional[str] = "af_heart"  # Default to Top-Rated af_heart
    rate: Optional[str] = "+0%"        # "-25%", "+0%", "+25%"
    mode: Optional[str] = "normal"     # "normal" or "split" (word-by-word with pauses)

class GenerateDrillsRequest(BaseModel):
    text: str
    tag: Optional[str] = "静静课文精选"

class SaveDrillsRequest(BaseModel):
    drills: List[Dict[str, Any]]

# ----------------- API Endpoints -----------------

@app.get("/api/status")
async def get_system_status():
    installed_models = get_installed_models()
    best_model = select_best_model(installed_models)
    kokoro_info = check_kokoro_status()
    return {
        "status": "online",
        "ollama_connected": len(installed_models) > 0,
        "models": installed_models,
        "active_model": best_model,
        "kokoro": kokoro_info
    }

@app.get("/api/scenarios")
async def get_scenarios():
    return SCENARIOS

@app.get("/api/drills")
async def get_drills(category: Optional[str] = None):
    custom = load_custom_drills()
    all_drills = custom + SENTENCE_DRILLS
    if category and category != "all":
        return [d for d in all_drills if d.get("category") == category]
    return all_drills

@app.get("/api/drills/custom")
async def get_custom_drills_endpoint():
    return load_custom_drills()

@app.post("/api/drills/custom/generate")
async def handle_generate_custom_drills(req: GenerateDrillsRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    drills = generate_drills_from_text(req.text, req.tag)
    return {"status": "success", "count": len(drills), "drills": drills}

@app.post("/api/drills/custom/save")
async def handle_save_custom_drills(req: SaveDrillsRequest):
    saved = save_custom_drills(req.drills)
    return {"status": "success", "total_custom": len(saved), "drills": saved}

@app.delete("/api/drills/custom")
async def handle_clear_custom_drills():
    delete_all_custom_drills()
    return {"status": "success", "message": "All custom drills cleared"}

@app.delete("/api/drills/custom/{drill_id}")
async def handle_delete_custom_drill(drill_id: str):
    if drill_id == "all":
        delete_all_custom_drills()
        return {"status": "success", "total_custom": 0}
    updated = delete_single_custom_drill(drill_id)
    return {"status": "success", "total_custom": len(updated)}

@app.post("/api/chat")
async def handle_chat(req: ChatRequest):
    scenario_info = next((s for s in SCENARIOS if s["id"] == req.scenario), None)
    context_prompt = scenario_info["prompt_context"] if scenario_info else ""
    
    result = chat_with_ollama(
        messages=req.messages,
        model_name=req.model,
        scenario_prompt=context_prompt
    )
    return result

@app.post("/api/chat/stream")
async def handle_chat_stream(req: ChatRequest):
    scenario_info = next((s for s in SCENARIOS if s["id"] == req.scenario), None)
    context_prompt = scenario_info["prompt_context"] if scenario_info else ""

    return StreamingResponse(
        stream_chat_with_ollama(
            messages=req.messages,
            model_name=req.model,
            scenario_prompt=context_prompt
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@app.post("/api/evaluate")
async def handle_evaluate(req: EvaluateRequest):
    result = evaluate_with_ollama(
        conversation=req.conversation,
        model_name=req.model
    )
    return result

class WarmupRequest(BaseModel):
    texts: List[str]

@app.post("/api/tts")
async def handle_tts(req: TTSRequest):
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    try:
        audio_bytes, mime_type, duration = await synthesize_speech(
            text=req.text,
            engine="kokoro",
            voice=req.voice or "af_heart",
            rate=req.rate or "+0%",
            mode=req.mode or "normal"
        )
        if not audio_bytes:
            raise HTTPException(status_code=500, detail="Synthesis failed")

        return Response(
            content=audio_bytes,
            media_type=mime_type,
            headers={
                "Cache-Control": "public, max-age=31536000, immutable",
                "Content-Disposition": "inline",
                "X-Audio-Duration": str(duration)
            }
        )
    except Exception as e:
        print(f"[TTS Error] {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/tts/warmup")
async def handle_tts_warmup(req: WarmupRequest, background_tasks: BackgroundTasks):
    async def _warm():
        for t in req.texts[:15]:
            try:
                await synthesize_speech(t)
            except Exception:
                pass
    background_tasks.add_task(_warm)
    return {"status": "warming_up", "count": len(req.texts[:15])}

@app.post("/api/transcribe")
async def handle_transcribe(file: UploadFile = File(...)):
    """
    Offline local transcription using faster-whisper.
    Guarantees 100% voice recognition even if browser SpeechRecognition is blocked.
    """
    try:
        with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name

        whisper = get_whisper()
        if not whisper:
            return {"status": "error", "text": "", "detail": "Whisper not initialized"}

        segments, info = whisper.transcribe(tmp_path, language="en", beam_size=3)
        transcribed_text = " ".join([s.text for s in segments]).strip()

        import os
import datetime
        try: os.unlink(tmp_path)
        except: pass

        return {"status": "success", "text": transcribed_text}
    except Exception as e:
        print(f"[Transcribe Error] {e}")
        return {"status": "error", "text": "", "detail": str(e)}

@app.get("/api/system/diagnostics")
async def get_system_diagnostics():
    """
    一键导出诊断日志：包含系统状态、Kokoro 语音模型状态以及最近 150 行服务日志
    """
    log_tail = []
    log_file = os.path.join(BASE_DIR, "data", "server.log")
    if os.path.exists(log_file):
        try:
            with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                log_tail = [line.strip() for line in lines[-150:]]
        except Exception as e:
            log_tail = [f"Failed to read server.log: {e}"]

    return {
        "status": "online",
        "timestamp": datetime.datetime.now().isoformat(),
        "kokoro": check_kokoro_status(),
        "recent_server_logs": log_tail
    }

# ----------------- Static Frontend -----------------

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")

if os.path.exists(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
