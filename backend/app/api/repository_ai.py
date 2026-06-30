from __future__ import annotations

from fastapi import APIRouter

from app.api.analyze import analyze_repository as run_analysis
from app.models.repository_ai import RepositoryAIResponse
from app.schemas import AnalyzeRequest
from app.services.repository_ai import generate_repository_ai

router = APIRouter(tags=["repository_ai"])


@router.post("/repository-ai", response_model=RepositoryAIResponse)
def repository_ai(request: AnalyzeRequest):
    analysis = run_analysis(request)

    if isinstance(analysis, dict):
        context = {
            "repo_path": analysis["repo_path"],
            "repo_hash": analysis["repo_hash"],
            "total_files": analysis["stats"]["total_files"],
            "files": analysis["files"],
            "stats": analysis["stats"],
            "graph_insights": analysis["graph_insights"],
            "dependency_map": analysis["dependency_map"],
        }
    else:
        context = {
            "repo_path": analysis.repo_path,
            "repo_hash": analysis.repo_hash,
            "total_files": analysis.stats.total_files,
            "files": [file.model_dump() for file in analysis.files],
            "stats": analysis.stats.model_dump(),
            "graph_insights": analysis.graph_insights.model_dump(),
            "dependency_map": analysis.dependency_map,
        }

    return generate_repository_ai(context)