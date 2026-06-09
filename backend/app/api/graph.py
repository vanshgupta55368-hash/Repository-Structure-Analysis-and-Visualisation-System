from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.core.cache import get_cached_analysis
from app.schemas import AnalysisResponse

router = APIRouter(tags=["graph"])


@router.get("/graph", response_model=AnalysisResponse)
def get_graph(repo_hash: str):
    cached = get_cached_analysis(repo_hash)
    if not cached:
        raise HTTPException(
            status_code=404,
            detail="Graph not found in cache. Run /analyze first.",
        )
    return cached