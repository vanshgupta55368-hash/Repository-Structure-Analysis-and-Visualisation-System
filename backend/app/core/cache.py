from __future__ import annotations

import json
import re
from pathlib import Path
from threading import Lock
from typing import Any

from app.core.config import get_settings

_LOCK = Lock()


class CacheManager:
    def __init__(self, cache_dir: Path):
        self.analysis_dir = cache_dir / "analysis"
        self.summary_dir = cache_dir / "summaries"

        self.analysis_dir.mkdir(parents=True, exist_ok=True)
        self.summary_dir.mkdir(parents=True, exist_ok=True)

    def _cache_name(self, key: str) -> str:
        """Return a filesystem-safe cache filename."""
        name = re.sub(r'[<>:"/\\|?*]+', "_", key.strip())
        return name.strip(" .") or "cache"

    def _analysis_file(self, repo_hash: str) -> Path:
        return self.analysis_dir / f"{self._cache_name(repo_hash)}.json"

    def _summary_file(self, file_hash: str) -> Path:
        return self.summary_dir / f"{self._cache_name(file_hash)}.json"

    def _read_json(self, file_path: Path) -> dict[str, Any] | None:
        if not file_path.exists():
            return None

        try:
            with file_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None

    def _write_json(self, file_path: Path, data: Any) -> None:
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with file_path.open("w", encoding="utf-8") as f:
            json.dump(
                data,
                f,
                indent=2,
                ensure_ascii=False,
                default=str,
            )

    def get_analysis(self, repo_hash: str) -> dict[str, Any] | None:
        with _LOCK:
            return self._read_json(
                self._analysis_file(repo_hash)
            )

    def set_analysis(self, repo_hash: str, data: Any) -> None:
        with _LOCK:
            self._write_json(
                self._analysis_file(repo_hash),
                data,
            )

    def get_summary(self, file_hash: str) -> str | None:
        with _LOCK:
            cached = self._read_json(
                self._summary_file(file_hash)
            )

            if cached is None:
                return None

            return cached.get("summary")

    def set_summary(self, file_hash: str, summary: str) -> None:
        with _LOCK:
            self._write_json(
                self._summary_file(file_hash),
                {"summary": summary},
            )

    def invalidate_analysis(self, repo_hash: str) -> None:
        with _LOCK:
            cache_file = self._analysis_file(repo_hash)

            if cache_file.exists():
                cache_file.unlink()

    def invalidate_summary(self, file_hash: str) -> None:
        with _LOCK:
            cache_file = self._summary_file(file_hash)

            if cache_file.exists():
                cache_file.unlink()


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