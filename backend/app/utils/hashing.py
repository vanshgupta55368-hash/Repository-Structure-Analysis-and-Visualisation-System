from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Iterable


def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()


def hash_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def hash_file(file_path: str | Path) -> str:
    path = Path(file_path)
    hasher = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def combine_hashes(hashes: Iterable[str]) -> str:
    joined = "|".join(sorted(hashes))
    return hash_text(joined)