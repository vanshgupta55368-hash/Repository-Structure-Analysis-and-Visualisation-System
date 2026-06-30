from __future__ import annotations

import json
import logging
from typing import Any

from app.core.config import get_settings
from app.services.architecture_summary import summarize_architecture
from app.services.repository_ai import generate_repository_ai

try:
    from google import genai  # type: ignore
except Exception:  # pragma: no cover
    genai = None


logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-2.5-flash"


def _safe_json(value: Any) -> str:
    """
    Safely serialize an object for inclusion in an LLM prompt.
    """
    try:
        return json.dumps(
            value,
            indent=2,
            ensure_ascii=False,
            default=str,
        )
    except Exception:
        return str(value)


def _extract_analysis_data(analysis: Any) -> dict[str, Any]:
    """
    Normalize both dict-based and model-based repository analyses
    into a common dictionary representation.
    """
    if isinstance(analysis, dict):
        return {
            "repo_path": analysis.get("repo_path", ""),
            "repo_hash": analysis.get("repo_hash", ""),
            "stats": analysis.get("stats", {}),
            "graph_insights": analysis.get("graph_insights", {}),
            "dependency_map": analysis.get("dependency_map", {}),
            "files": analysis.get("files", []),
        }

    return {
        "repo_path": getattr(analysis, "repo_path", ""),
        "repo_hash": getattr(analysis, "repo_hash", ""),
        "stats": analysis.stats.model_dump(),
        "graph_insights": analysis.graph_insights.model_dump(),
        "dependency_map": analysis.dependency_map,
        "files": [file.model_dump() for file in analysis.files],
    }


def build_chat_prompt(
    repository_context: dict[str, Any],
    question: str,
) -> str:
    """
    Build the prompt sent to Gemini for repository Q&A.
    """
    context_text = _safe_json(repository_context)

    return f"""
You are helping a developer understand a repository.

Use only the repository information below.

Do not guess if the answer is not supported by the context.

If the context is insufficient, explicitly say so.

Write the answer in Markdown.

Try to be practical and specific.

If useful, mention:

- the most relevant file(s)
- why they matter
- the next file the person should read

Return the answer in this format:

### Answer
...

### Why
...

### Related Files
- ...

### Suggested Next Step
...

Repository context:

{context_text}

Question:

{question}
""".strip()


def _generate_with_gemini(
    prompt: str,
    api_key: str,
) -> str | None:
    """
    Generate a response using the Gemini SDK.
    Returns None if no usable response is produced.
    """
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model=DEFAULT_MODEL,
        contents=prompt,
    )

    text = getattr(response, "text", "") or ""
    text = text.strip()

    return text or None


def ask_repository_question(
    repository_context: dict[str, Any],
    question: str,
) -> str:
    """
    Answer repository questions using Gemini and the repository context.
    """
    settings = get_settings()

    if not settings.gemini_api_key:
        return "Gemini API key not configured."

    if genai is None:
        return "Gemini SDK is unavailable."

    prompt = build_chat_prompt(
        repository_context=repository_context,
        question=question,
    )

    try:
        logger.info("Generating repository answer using Gemini.")

        response = _generate_with_gemini(
            prompt=prompt,
            api_key=settings.gemini_api_key,
        )

        if response is not None:
            logger.info("Repository answer generated successfully.")
            return response

        logger.warning(
            "Gemini returned an empty response for a repository question."
        )
        return "I could not generate a useful answer from the repository context."

    except Exception:
        logger.exception("Failed to generate repository answer.")
        return "Failed to generate repository answer due to an internal error."


def build_repository_context(analysis: Any) -> dict[str, Any]:
    """
    Build a rich context object used by the repository chat service.

    The returned context combines:
    - repository statistics
    - graph insights
    - dependency information
    - architecture summary
    - repository intelligence
    """
    data = _extract_analysis_data(analysis)

    repo_path = data["repo_path"]
    repo_hash = data["repo_hash"]
    stats = data["stats"]
    graph_insights = data["graph_insights"]
    dependency_map = data["dependency_map"]
    files = data["files"]

    repository_data = {
        "repo_path": repo_path,
        "repo_hash": repo_hash,
        "stats": stats,
        "graph_insights": graph_insights,
        "dependency_map": dependency_map,
        "files": files,
        "total_files": stats.get("total_files", len(files)),
    }

    architecture_summary = summarize_architecture(repository_data)
    repository_ai = generate_repository_ai(repository_data)

    top_files = [
        {
            "id": file.get("id"),
            "name": file.get("name"),
            "path": file.get("path"),
            "language": file.get("language"),
            "complexity": file.get("complexity", 0),
        }
        for file in files[:12]
    ]

    return {
        "repo_path": repo_path,
        "repo_hash": repo_hash,
        "stats": stats,
        "graph_insights": graph_insights,
        "dependency_map": dependency_map,
        "top_files": top_files,
        "top_complex_files": (stats.get("top_complex_files") or [])[:8],
        "architecture_summary": architecture_summary,
        "repository_intelligence": repository_ai,
        "question_help": [
            "Where should I start reading this repository?",
            "Which files are the most important?",
            "Which files are the most complex?",
            "Explain the architecture.",
            "Which module should I refactor first?",
        ],
    }