from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.api.analyze import analyze_repository as run_analysis
from app.models.repository_chat import (
    RepositoryChatRequest,
    RepositoryChatResponse,
)
from app.services.repository_chat import (
    ask_repository_question,
    build_repository_context,
)

router = APIRouter(tags=["repository_chat"])


@router.post("/repository-chat", response_model=RepositoryChatResponse)
def repository_chat(request: RepositoryChatRequest):
    try:
        analysis = run_analysis(request)
        repository_context = build_repository_context(analysis)

        answer = ask_repository_question(
            repository_context=repository_context,
            question=request.question,
        )

        return RepositoryChatResponse(answer=answer)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))