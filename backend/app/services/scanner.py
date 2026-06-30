from __future__ import annotations

import os
from pathlib import Path

from app.core.config import get_settings
from app.core.constants import (
    IGNORED_DIRECTORIES,
    IGNORED_FILES,
    SUPPORTED_LANGUAGE_EXTENSIONS,
)
from app.models.file_model import FileNode
from app.utils.file_utils import get_extension, is_text_file, normalize_path
from app.utils.hashing import hash_file


def should_ignore_directory(name: str) -> bool:
    return name.startswith(".") or name in IGNORED_DIRECTORIES


def build_file_node(repo_root: Path, file_path: Path) -> FileNode:
    relative_path = file_path.relative_to(repo_root).as_posix()
    extension = get_extension(file_path)

    return FileNode(
        id=relative_path,
        name=file_path.name,
        path=relative_path,
        language=SUPPORTED_LANGUAGE_EXTENSIONS.get(extension, "unknown"),
        extension=extension,
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

    scanned_files: list[FileNode] = []

    for root, dirs, file_names in os.walk(repo_root):
        dirs[:] = [d for d in dirs if not should_ignore_directory(d)]

        folder = Path(root)

        for name in file_names:
            file_path = folder / name

            if (
                name in IGNORED_FILES
                or name.startswith("~$")
            ):
                continue

            try:
                if file_path.stat().st_size > settings.max_file_size_bytes:
                    continue
            except OSError:
                continue

            if not is_text_file(file_path):
                continue

            try:
                scanned_files.append(build_file_node(repo_root, file_path))
            except OSError:
                continue

    scanned_files.sort(key=lambda node: node.path)
    return scanned_files


def index_files_by_path(files: list[FileNode]) -> dict[str, FileNode]:
    index: dict[str, FileNode] = {}

    for file in files:
        index[file.id] = file
        index[file.path] = file
        index[normalize_path(file.path)] = file
        index[file.name] = file
        index[Path(file.name).stem] = file

        module = Path(file.path).with_suffix("")
        if module.parts:
            index[".".join(module.parts)] = file
            index["/".join(module.parts)] = file

    return index