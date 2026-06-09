from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable


class BaseParser(ABC):
    supported_extensions: set[str] = set()

    @classmethod
    def can_parse(cls, file_path: str | Path) -> bool:
        return Path(file_path).suffix.lower() in cls.supported_extensions

    @abstractmethod
    def extract_dependencies(self, code: str, file_path: str | None = None) -> list[str]:
        raise NotImplementedError

    def extract_symbols(self, code: str) -> dict[str, list[str]]:
        return {
            "functions": [],
            "classes": [],
            "imports": [],
        }


def unique_sorted(items: Iterable[str]) -> list[str]:
    return sorted({item.strip() for item in items if item and item.strip()})