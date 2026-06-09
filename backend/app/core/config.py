from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from app.core.constants import IGNORED_DIRECTORIES, MAX_FILE_SIZE_BYTES


@dataclass(frozen=True)
class Settings:
    app_name: str = "Repo Visualizer Backend"
    app_version: str = "1.0.0"
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"

    cache_dir: Path = field(
        default_factory=lambda: Path(os.getenv("CACHE_DIR", ".cache")).resolve()
    )

    ignored_directories: set[str] = field(default_factory=lambda: set(IGNORED_DIRECTORIES))
    max_file_size_bytes: int = int(os.getenv("MAX_FILE_SIZE_BYTES", str(MAX_FILE_SIZE_BYTES)))

    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY")
    cors_origins: list[str] = field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv("CORS_ORIGINS", "*").split(",")
            if origin.strip()
        ]
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.cache_dir.mkdir(parents=True, exist_ok=True)
    return settings