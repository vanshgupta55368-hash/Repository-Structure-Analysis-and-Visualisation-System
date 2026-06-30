from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.analyze import router as analyze_router
from app.api.architecture import router as architecture_router
from app.api.graph import router as graph_router
from app.api.health import router as health_router
from app.api.repository_ai import router as repository_ai_router
from app.api.repository_chat import router as repository_chat_router
from app.api.summary import router as summary_router
from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
    )

    origins = ["*"] if "*" in settings.cors_origins else settings.cors_origins

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health_router)
    app.include_router(analyze_router)
    app.include_router(graph_router)
    app.include_router(summary_router)
    app.include_router(repository_ai_router)
    app.include_router(architecture_router)
    app.include_router(repository_chat_router)

    return app


app = create_app()