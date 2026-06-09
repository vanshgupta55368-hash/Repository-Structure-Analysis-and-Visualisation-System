from __future__ import annotations

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