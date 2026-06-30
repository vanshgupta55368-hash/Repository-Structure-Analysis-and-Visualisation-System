from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.core.config import get_settings

try:
    from google import genai as google_genai  # type: ignore
except Exception:  # pragma: no cover
    google_genai = None

try:
    import google.generativeai as legacy_genai  # type: ignore
except Exception:  # pragma: no cover
    legacy_genai = None


DEFAULT_MODEL_NAME = "gemini-2.5-flash"


def _dedupe_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        item = str(item).strip()
        if not item or item in seen:
            continue
        seen.add(item)
        result.append(item)
    return result


def _extract_json_payload(text: str) -> dict[str, Any] | None:
    cleaned = text.strip()

    # Remove markdown fences if the model adds them.
    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    # Try to extract the first JSON object from the text.
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    return None


def build_architecture_prompt(context: dict[str, Any]) -> str:
    context_text = json.dumps(context, indent=2, ensure_ascii=False, default=str)

    return f"""
You are a senior software architect analyzing a code repository.

Return ONLY valid JSON with exactly these keys:
{{
  "overview": "string",
  "main_modules": ["string"],
  "hotspots": ["string"],
  "refactoring_suggestions": ["string"]
}}

Rules:
- overview should be 3 to 6 sentences.
- main_modules should list the most important files/modules in the repository.
- hotspots should list the files that are most central, complex, or risky.
- refactoring_suggestions should be specific and actionable.
- Do not wrap the output in markdown fences.
- Do not add any extra keys.
- Do not include commentary outside the JSON.

Repository context:
{context_text}
""".strip()


def _local_architecture_summary(context: dict[str, Any]) -> dict[str, Any]:
    stats = context.get("stats", {})
    graph_insights = context.get("graph_insights", {})
    language_breakdown = context.get("language_breakdown", {})
    files = context.get("files", [])

    top_complex_files = stats.get("top_complex_files", []) or []
    top_complex_names = [
        str(item.get("file"))
        for item in top_complex_files
        if isinstance(item, dict) and item.get("file")
    ]

    top_incoming = [
        str(item.get("file"))
        for item in graph_insights.get("top_incoming", [])
        if isinstance(item, dict) and item.get("file")
    ]

    top_outgoing = [
        str(item.get("file"))
        for item in graph_insights.get("top_outgoing", [])
        if isinstance(item, dict) and item.get("file")
    ]

    cycles = graph_insights.get("cycles", []) or []
    isolated_files = graph_insights.get("isolated_files", []) or []

    main_modules = _dedupe_keep_order(top_complex_names + top_incoming + top_outgoing)[:6]
    hotspots = _dedupe_keep_order(top_incoming + top_complex_names + top_outgoing)[:8]

    suggestions: list[str] = []

    if cycles:
        suggestions.append(
            "Break circular dependencies between the modules involved in the detected cycles."
        )

    if top_complex_names:
        suggestions.append(
            "Split the most complex modules into smaller, single-responsibility services."
        )

    if isolated_files:
        suggestions.append(
            "Review isolated files and remove dead code or connect them to the main pipeline."
        )

    if not suggestions:
        suggestions.append(
            "Consider extracting shared logic into smaller services to reduce coupling."
        )

    total_files = int(context.get("total_files", len(files)))
    total_languages = len(language_breakdown)

    overview = (
        f"This repository contains {total_files} files across {total_languages} language groups. "
        f"The architecture centers on repository scanning, dependency extraction, metrics collection, "
        f"graph building, and AI summaries. "
        f"The most visible technical pressure appears in {', '.join(main_modules[:3]) if main_modules else 'the core analysis pipeline'}."
    )

    return {
        "overview": overview,
        "main_modules": main_modules,
        "hotspots": hotspots,
        "refactoring_suggestions": suggestions,
    }


def _normalize_architecture_payload(
    data: dict[str, Any] | None,
    context: dict[str, Any],
) -> dict[str, Any]:
    fallback = _local_architecture_summary(context)

    if not isinstance(data, dict):
        return fallback

    def as_list(value: Any) -> list[str]:
        if isinstance(value, list):
            return _dedupe_keep_order([str(x) for x in value])
        return []

    overview = str(data.get("overview") or fallback["overview"])
    main_modules = as_list(data.get("main_modules")) or fallback["main_modules"]
    hotspots = as_list(data.get("hotspots")) or fallback["hotspots"]
    refactoring_suggestions = as_list(data.get("refactoring_suggestions")) or fallback[
        "refactoring_suggestions"
    ]

    return {
        "overview": overview,
        "main_modules": main_modules,
        "hotspots": hotspots,
        "refactoring_suggestions": refactoring_suggestions,
    }


def summarize_architecture(context: dict[str, Any]) -> dict[str, Any]:
    """
    Returns a structured architecture summary.
    Tries Google GenAI first, then falls back to the legacy SDK, then to local heuristics.
    """
    prompt = build_architecture_prompt(context)
    fallback = _local_architecture_summary(context)

    settings = get_settings()
    if not settings.gemini_api_key:
        return fallback

    try:
        print("USING GEMINI FOR ARCHITECTURE...")

        text = ""

        if google_genai is not None:
            client = google_genai.Client(api_key=settings.gemini_api_key)
            response = client.models.generate_content(
                model=DEFAULT_MODEL_NAME,
                contents=prompt,
            )
            text = getattr(response, "text", "") or ""

        elif legacy_genai is not None:
            legacy_genai.configure(api_key=settings.gemini_api_key)
            model = legacy_genai.GenerativeModel(DEFAULT_MODEL_NAME)
            response = model.generate_content(prompt)
            text = getattr(response, "text", "") or ""

        else:
            return fallback

        if not text.strip():
            print("ARCHITECTURE GEMINI EMPTY RESPONSE")
            return fallback

        parsed = _extract_json_payload(text)
        return _normalize_architecture_payload(parsed, context)

    except Exception as e:
        print("ARCHITECTURE GEMINI ERROR:", repr(e))
        return fallback