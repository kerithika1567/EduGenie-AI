import os
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import pages, qa, explain, quiz, summarize, path
from app.services import local_model_service

# Setup application logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("edugenie.main")

app = FastAPI(
    title="EduGenie AI Learning Assistant",
    description="Interactive AI learning assistant powered by Gemini API and optional local LaMini-Flan-T5 model.",
    version="1.0.0"
)

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files mounting
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR, exist_ok=True)
    os.makedirs(os.path.join(STATIC_DIR, "css"), exist_ok=True)
    os.makedirs(os.path.join(STATIC_DIR, "js"), exist_ok=True)

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Include Routers
app.include_router(pages.router)
app.include_router(qa.router)
app.include_router(explain.router)
app.include_router(quiz.router)
app.include_router(summarize.router)
app.include_router(path.router)

@app.get("/health", tags=["Health Check"])
async def health_check():
    """
    Health check endpoint returning system status, Gemini configuration, and local model state.
    """
    has_api_key = bool(settings.gemini_api_key and settings.gemini_api_key.strip() not in ("", "your_gemini_api_key_here"))
    local_status = local_model_service.get_local_model_status()
    
    return {
        "status": "ok",
        "app": "EduGenie AI Learning Assistant",
        "gemini_configured": has_api_key,
        "gemini_model": settings.gemini_model,
        "local_model_status": local_status
    }
