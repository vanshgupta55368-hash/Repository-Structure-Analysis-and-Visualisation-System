from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.core.cache import get_cached_summary, set_cached_summary
from app.schemas import (
    FileSummaryRequest,
    FileSummaryResponse,
    RepositorySummaryRequest,
    RepositorySummaryResponse,
)
from app.services.ai_summary import summarize_file, summarize_repository
from app.services.scanner import scan_repository
from app.utils.file_utils import is_binary_file, read_file
from app.utils.hashing import combine_hashes, hash_file

router = APIRouter(tags=["summary"])


def _resolve_file_path(repo_root: Path, requested_path: str) -> Path:
    candidate = Path(requested_path)

    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        resolved = (repo_root / candidate).resolve()

    repo_root_resolved = repo_root.resolve()

    if resolved != repo_root_resolved and repo_root_resolved not in resolved.parents:
        raise HTTPException(
            status_code=400,
            detail="File path must stay inside the repository root",
        )

    return resolved


@router.post("/summary/file", response_model=FileSummaryResponse)
def summarize_single_file(request: FileSummaryRequest):
    repo_root = Path(request.repo_path).resolve()

    if not repo_root.exists():
        raise HTTPException(status_code=404, detail="Repository path does not exist")
    if not repo_root.is_dir():
        raise HTTPException(status_code=400, detail="Repository path is not a directory")

    file_path = _resolve_file_path(repo_root, request.file_path)

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    if file_path.is_dir():
        raise HTTPException(status_code=400, detail="Expected a file, got a directory")
    if is_binary_file(file_path):
        raise HTTPException(status_code=400, detail="Binary files are not supported for summaries")

    code = read_file(file_path)
    language = file_path.suffix.lower().lstrip(".") or "unknown"
    if language == "py":
        language = "python"
    elif language in {"cpp", "cc", "cxx", "hpp", "hh", "h"}:
        language = "cpp"
    else:
        language = "unknown"

    file_hash = hash_file(file_path)
    cached = get_cached_summary(file_hash)
    summary = summarize_file(
        code=code,
        language=language,
        file_path=str(file_path),
        use_cache_key=file_hash,
    )

    return FileSummaryResponse(
        repo_path=str(repo_root),
        file_path=str(file_path),
        language=language,
        size=file_path.stat().st_size,
        file_hash=file_hash,
        cached=cached is not None,
        summary=summary,
    )


@router.post("/summary/repository", response_model=RepositorySummaryResponse)
def summarize_repository_endpoint(request: RepositorySummaryRequest):
    repo_root = Path(request.repo_path).resolve()

    if not repo_root.exists():
        raise HTTPException(status_code=404, detail="Repository path does not exist")
    if not repo_root.is_dir():
        raise HTTPException(status_code=400, detail="Repository path is not a directory")

    files = scan_repository(repo_root)

    repo_hash = combine_hashes([f.file_hash or "" for f in files])
    cached = get_cached_summary(repo_hash)

    if cached:
        return RepositorySummaryResponse(
            repo_path=str(repo_root),
            total_files=len(files),
            language_breakdown=_language_breakdown(files),
            cached=True,
            summary=cached,
        )

    summary = summarize_repository([f.model_dump() for f in files])
    set_cached_summary(repo_hash, summary)

    return RepositorySummaryResponse(
        repo_path=str(repo_root),
        total_files=len(files),
        language_breakdown=_language_breakdown(files),
        cached=False,
        summary=summary,
    )


def _language_breakdown(files) -> dict[str, int]:
    counts: dict[str, int] = {}
    for f in files:
        lang = getattr(f, "language", "unknown") or "unknown"
        counts[lang] = counts.get(lang, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))