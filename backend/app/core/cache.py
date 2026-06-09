from __future__ import annotations

import json
from pathlib import Path
from threading import Lock
from typing import Any

from app.core.config import get_settings

_LOCK = Lock()


class CacheManager:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.analysis_dir = self.base_dir / "analysis"
        self.summary_dir = self.base_dir / "summaries"
        self.analysis_dir.mkdir(parents=True, exist_ok=True)
        self.summary_dir.mkdir(parents=True, exist_ok=True)

    def _read_json(self, path: Path) -> dict[str, Any] | None:
        if not path.exists():
            return None
        try:
            with path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def _write_json(self, path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

    def get_analysis(self, repo_hash: str) -> dict[str, Any] | None:
        with _LOCK:
            return self._read_json(self.analysis_dir / f"{repo_hash}.json")

    def set_analysis(self, repo_hash: str, data: Any) -> None:
        with _LOCK:
            self._write_json(self.analysis_dir / f"{repo_hash}.json", data)

    def get_summary(self, file_hash: str) -> str | None:
        with _LOCK:
            data = self._read_json(self.summary_dir / f"{file_hash}.json")
            if not data:
                return None
            return data.get("summary")

    def set_summary(self, file_hash: str, summary: str) -> None:
        with _LOCK:
            self._write_json(self.summary_dir / f"{file_hash}.json", {"summary": summary})

    def invalidate_analysis(self, repo_hash: str) -> None:
        with _LOCK:
            p = self.analysis_dir / f"{repo_hash}.json"
            if p.exists():
                p.unlink()

    def invalidate_summary(self, file_hash: str) -> None:
        with _LOCK:
            p = self.summary_dir / f"{file_hash}.json"
            if p.exists():
                p.unlink()


_settings = get_settings()
cache_manager = CacheManager(_settings.cache_dir)


def get_cached_analysis(repo_hash: str):
    return cache_manager.get_analysis(repo_hash)


def set_cached_analysis(repo_hash: str, data):
    cache_manager.set_analysis(repo_hash, data)


def get_cached_summary(file_hash: str):
    return cache_manager.get_summary(file_hash)


def set_cached_summary(file_hash: str, summary: str):
    cache_manager.set_summary(file_hash, summary)