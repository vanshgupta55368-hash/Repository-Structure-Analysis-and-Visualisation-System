from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.core.cache import get_cached_summary, set_cached_summary
from app.models.file_model import FileNode
from app.models.metrics_model import FileMetrics
from app.parsers.cpp_parser import cpp_parser
from app.parsers.python_parser import python_parser
from app.schemas import (
    AnalysisStats,
    ArchitectureSummaryRequest,
    ArchitectureSummaryResponse,
)
from app.services.architecture_summary import summarize_architecture
from app.services.graph_builder import build_graph
from app.services.graph_insights import analyze_graph
from app.services.metrics import compute_file_metrics, compute_repo_metrics
from app.services.scanner import scan_repository
from app.utils.file_utils import read_file
from app.utils.hashing import combine_hashes

router = APIRouter(tags=["architecture"])


def _get_dependencies(file: FileNode, code: str) -> list[str]:
    if file.language == "python":
        return python_parser.extract_dependencies(code, file.path)
    if file.language == "cpp":
        return cpp_parser.extract_dependencies(code, file.path)
    return []


def _build_repo_hash(files: list[FileNode]) -> str:
    file_hashes = [file.file_hash or "" for file in files]
    return combine_hashes(file_hashes)


def _language_breakdown(files: list[FileNode]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for file in files:
        lang = file.language or "unknown"
        counts[lang] = counts.get(lang, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


@router.post("/summary/architecture", response_model=ArchitectureSummaryResponse)
def summarize_repository_architecture(request: ArchitectureSummaryRequest):
    repo_root = Path(request.repo_path).resolve()

    if not repo_root.exists():
        raise HTTPException(status_code=404, detail="Repository path does not exist")
    if not repo_root.is_dir():
        raise HTTPException(status_code=400, detail="Repository path is not a directory")

    files = scan_repository(repo_root)
    repo_hash = _build_repo_hash(files)

    cache_key = f"architecture_{repo_hash}"
    cached = get_cached_summary(cache_key)
    if cached:
        try:
            cached_data = json.loads(cached)
            cached_data["cached"] = True
            return ArchitectureSummaryResponse(**cached_data)
        except Exception:
            pass

    dependency_map: dict[str, list[str]] = {}
    file_metrics: dict[str, FileMetrics] = {}

    for file in files:
        file_path = repo_root / file.path
        code = read_file(file_path)

        dependency_map[file.id] = _get_dependencies(file, code)
        file_metrics[file.id] = compute_file_metrics(file_path, file.language)

    graph = build_graph(
        files=files,
        dependency_map=dependency_map,
        metrics_by_file=file_metrics,
    )
    stats_dict = compute_repo_metrics(file_metrics)
    graph_insights = analyze_graph(files, graph.edges)

    architecture_context = {
        "repo_path": str(repo_root),
        "repo_hash": repo_hash,
        "total_files": len(files),
        "language_breakdown": _language_breakdown(files),
        "stats": stats_dict,
        "graph_insights": graph_insights.model_dump(),
        "files": [file.model_dump() for file in files[:20]],
    }

    architecture = summarize_architecture(architecture_context)

    response = ArchitectureSummaryResponse(
        repo_path=str(repo_root),
        repo_hash=repo_hash,
        cached=False,
        total_files=len(files),
        language_breakdown=_language_breakdown(files),
        stats=AnalysisStats(
            total_files=len(files),
            total_loc=stats_dict["total_loc"],
            total_blank_lines=stats_dict["total_blank_lines"],
            total_comment_lines=stats_dict["total_comment_lines"],
            total_code_lines=stats_dict["total_code_lines"],
            total_complexity=stats_dict["total_complexity"],
            average_complexity=stats_dict["average_complexity"],
            top_complex_files=stats_dict["top_complex_files"],
        ),
        graph_insights=graph_insights,
        overview=architecture["overview"],
        main_modules=architecture["main_modules"],
        hotspots=architecture["hotspots"],
        refactoring_suggestions=architecture["refactoring_suggestions"],
    )

    set_cached_summary(cache_key, response.model_dump_json())
    return response