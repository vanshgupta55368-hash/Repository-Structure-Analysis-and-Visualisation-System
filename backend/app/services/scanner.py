from __future__ import annotations

import os
from pathlib import Path

from app.core.config import get_settings
from app.core.constants import IGNORED_DIRECTORIES, IGNORED_FILES, SUPPORTED_LANGUAGE_EXTENSIONS
from app.models.file_model import FileNode
from app.utils.file_utils import get_extension, is_text_file, normalize_path
from app.utils.hashing import hash_file


def should_ignore_directory(directory_name: str) -> bool:
    return directory_name in IGNORED_DIRECTORIES or directory_name.startswith(".")


def should_ignore_file(file_path: Path) -> bool:
    if file_path.name in IGNORED_FILES:
        return True
    if file_path.name.startswith("~$"):
        return True
    return False


def detect_language(file_path: str | Path) -> str:
    ext = get_extension(file_path)
    return SUPPORTED_LANGUAGE_EXTENSIONS.get(ext, "unknown")


def build_file_node(repo_root: Path, file_path: Path) -> FileNode:
    rel_path = file_path.relative_to(repo_root).as_posix()
    ext = get_extension(file_path)
    language = detect_language(file_path)

    return FileNode(
        id=rel_path,
        name=file_path.name,
        path=rel_path,
        language=language,
        extension=ext,
        size=file_path.stat().st_size,
        file_hash=hash_file(file_path),
    )


def scan_repository(repo_path: str | Path) -> list[FileNode]:
    settings = get_settings()
    repo_root = Path(repo_path).resolve()

    if not repo_root.exists():
        raise FileNotFoundError(f"Repository path does not exist: {repo_root}")

    if not repo_root.is_dir():
        raise NotADirectoryError(f"Repository path is not a directory: {repo_root}")

    files: list[FileNode] = []

    for root, dirs, filenames in os.walk(repo_root):
        dirs[:] = [d for d in dirs if not should_ignore_directory(d)]
        current_dir = Path(root)

        for filename in filenames:
            file_path = current_dir / filename

            if should_ignore_file(file_path):
                continue

            try:
                if file_path.stat().st_size > settings.max_file_size_bytes:
                    continue
            except OSError:
                continue

            if not is_text_file(file_path):
                continue

            try:
                files.append(build_file_node(repo_root, file_path))
            except OSError:
                continue

    files.sort(key=lambda x: x.path)
    return files


def index_files_by_path(files: list[FileNode]) -> dict[str, FileNode]:
    index: dict[str, FileNode] = {}

    for file in files:
        normalized = normalize_path(file.path)
        index[file.id] = file
        index[file.path] = file
        index[normalized] = file
        index[file.name] = file
        index[Path(file.name).stem] = file

        parts = Path(file.path).with_suffix("").parts
        if parts:
            index[".".join(parts)] = file
            index["/".join(parts)] = file

    return index