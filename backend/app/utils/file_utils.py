from __future__ import annotations

from pathlib import Path
from typing import Iterable

from app.core.constants import DEFAULT_ENCODING


def normalize_path(file_path: str | Path) -> str:
    return Path(file_path).resolve().as_posix()


def safe_join(base_path: str | Path, *parts: str) -> Path:
    return Path(base_path).joinpath(*parts).resolve()


def get_extension(file_path: str | Path) -> str:
    return Path(file_path).suffix.lower()


def is_binary_file(file_path: str | Path) -> bool:
    path = Path(file_path)
    try:
        with path.open("rb") as f:
            chunk = f.read(4096)
        return b"\x00" in chunk
    except OSError:
        return True


def is_text_file(file_path: str | Path) -> bool:
    return not is_binary_file(file_path)


def read_file(file_path: str | Path) -> str:
    path = Path(file_path)
    with path.open("r", encoding=DEFAULT_ENCODING, errors="ignore") as f:
        return f.read()


def iter_lines(file_path: str | Path) -> Iterable[str]:
    content = read_file(file_path)
    return content.splitlines()