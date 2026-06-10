from __future__ import annotations
from app.core.config import get_settings
from fastapi import APIRouter

from app.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    settings = get_settings()
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "debug": settings.debug,
    }
@router.get("/debug/gemini")
def debug_gemini():
    settings = get_settings()

    return {
        "gemini_configured": bool(settings.gemini_api_key),
        "key_prefix": settings.gemini_api_key[:8] if settings.gemini_api_key else None,
    }