from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.core.cache import get_cached_analysis, set_cached_analysis
from app.models.file_model import FileNode
from app.models.metrics_model import FileMetrics
from app.parsers.cpp_parser import cpp_parser
from app.parsers.python_parser import python_parser
from app.schemas import AnalyzeRequest, AnalysisResponse, AnalysisStats
from app.services.graph_builder import build_graph
from app.services.graph_insights import analyze_graph
from app.services.metrics import compute_file_metrics, compute_repo_metrics
from app.services.scanner import scan_repository
from app.utils.file_utils import read_file
from app.utils.hashing import combine_hashes

router = APIRouter(tags=["analysis"])


def _get_dependencies(file: FileNode, code: str) -> list[str]:
    if file.language == "python":
        return python_parser.extract_dependencies(code, file.path)
    if file.language == "cpp":
        return cpp_parser.extract_dependencies(code, file.path)
    return []


def _build_repo_hash(files: list[FileNode]) -> str:
    file_hashes = [file.file_hash or "" for file in files]
    return combine_hashes(file_hashes)


@router.post("/analyze", response_model=AnalysisResponse)
def analyze_repository(request: AnalyzeRequest):
    repo_path = Path(request.repo_path).resolve()

    if not repo_path.exists():
        raise HTTPException(status_code=404, detail="Repository path does not exist")
    if not repo_path.is_dir():
        raise HTTPException(status_code=400, detail="Repository path is not a directory")

    files = scan_repository(repo_path)
    repo_hash = _build_repo_hash(files)

    cached = get_cached_analysis(repo_hash)
    if cached:
        return cached

    dependency_map: dict[str, list[str]] = {}
    file_metrics: dict[str, FileMetrics] = {}

    for file in files:
        file_path = repo_path / file.path
        code = read_file(file_path)

        dependency_map[file.id] = _get_dependencies(file, code)
        file_metrics[file.id] = compute_file_metrics(file_path, file.language)

    graph = build_graph(files=files, dependency_map=dependency_map, metrics_by_file=file_metrics)
    stats_dict = compute_repo_metrics(file_metrics)
    graph_insights = analyze_graph(files, graph.edges)

    response = AnalysisResponse(
        repo_path=str(repo_path),
        files=files,
        nodes=graph.nodes,
        edges=graph.edges,
        file_metrics=file_metrics,
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
        repo_hash=repo_hash,
        dependency_map=dependency_map,
    )

    set_cached_analysis(repo_hash, response.model_dump())
    return response