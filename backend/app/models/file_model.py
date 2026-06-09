from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class FileNode(BaseModel):
    """
    Canonical representation of one file inside a repository.
    This is the most important data object in the whole backend.
    """

    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="Stable unique file identifier, usually repo-relative path")
    name: str = Field(..., description="File name with extension")
    path: str = Field(..., description="Repository-relative normalized path")
    language: str = Field(default="unknown", description="Detected language")
    extension: str = Field(default="", description="File extension")
    size: int = Field(default=0, ge=0, description="File size in bytes")
    file_hash: Optional[str] = Field(default=None, description="SHA-256 hash of the file content")
    is_binary: bool = Field(default=False, description="Whether the file is binary")
    line_count: int = Field(default=0, ge=0, description="Total number of lines")
    last_modified: Optional[datetime] = Field(default=None, description="Last modification time")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extra file metadata")


class FileScanResult(BaseModel):
    """
    Result produced by the repository scanner.
    """

    model_config = ConfigDict(extra="ignore")

    repo_path: str
    scanned_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_files: int = Field(default=0, ge=0)
    ignored_files: int = Field(default=0, ge=0)
    files: list[FileNode] = Field(default_factory=list)
    ignored_paths: list[str] = Field(default_factory=list)


class RepositoryInfo(BaseModel):
    """
    Small summary about the scanned repository.
    """

    model_config = ConfigDict(extra="ignore")

    repo_path: str
    repo_hash: str = ""
    total_files: int = 0
    total_size_bytes: int = 0
    languages: dict[str, int] = Field(default_factory=dict)