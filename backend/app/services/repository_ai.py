from __future__ import annotations

import hashlib
import json
import logging
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


logger = logging.getLogger(__name__)

DEFAULT_MODEL_NAME = "gemini-2.5-flash"
CACHE_NAMESPACE = "repository_ai"

MAX_SCORE = 100
MIN_SCORE = 40

HIGH_SCORE_THRESHOLD = 85
MODERATE_SCORE_THRESHOLD = 70

MAX_RECOMMENDATIONS = 5
MAX_HOTSPOTS = 3

COMPLEXITY_PENALTY_DIVISOR = 2
CYCLE_PENALTY_PER_ITEM = 5
TOP_COMPLEX_PENALTY_PER_ITEM = 2
ISOLATED_FILE_PENALTY_PER_ITEM = 1

HIGH_SEVERITY = "High"
MEDIUM_SEVERITY = "Medium"
LOW_SEVERITY = "Low"


def _dedupe_keep_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for item in items:
        value = str(item).strip()
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)

    return result


def _safe_filename(key: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*]+', "_", key.strip())
    cleaned = cleaned.strip(" .")
    return cleaned or "cache"


def _extract_json_payload(text: str) -> dict[str, Any] | None:
    cleaned = text.strip()

    cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*```$", "", cleaned)

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except Exception:
        pass

    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

    return None


def _cache_dir() -> Path:
    settings = get_settings()
    repo_ai_dir = settings.cache_dir / CACHE_NAMESPACE
    repo_ai_dir.mkdir(parents=True, exist_ok=True)
    return repo_ai_dir


def _cache_file(cache_key: str) -> Path:
    return _cache_dir() / f"{_safe_filename(cache_key)}.json"


def _cache_key_for_context(context: dict[str, Any]) -> str:
    raw = json.dumps(context, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _read_cache(cache_key: str) -> dict[str, Any] | None:
    path = _cache_file(cache_key)
    if not path.exists():
        return None

    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    return None


def _write_cache(cache_key: str, data: dict[str, Any]) -> None:
    path = _cache_file(cache_key)
    try:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    except Exception:
        pass


def _cache_and_return(cache_key: str, data: dict[str, Any]) -> dict[str, Any]:
    _write_cache(cache_key, data)
    return data


def build_repository_ai_prompt(context: dict[str, Any]) -> str:
    context_text = json.dumps(context, indent=2, ensure_ascii=False, default=str)

    return f"""
You are a senior software architect reviewing a repository intelligence dashboard.

Return ONLY valid JSON with exactly these keys:

{{
  "health": {{
    "score": 0,
    "maintainability": "string",
    "architecture": "string",
    "complexity": "string",
    "summary": "string"
  }},
  "recommendations": [
    {{
      "title": "string",
      "description": "string"
    }}
  ],
  "hotspots": [
    {{
      "file": "string",
      "reason": "string",
      "severity": "string"
    }}
  ]
}}

Rules:
- score must be an integer from 0 to 100.
- Return exactly 5 recommendations.
- Return exactly 3 hotspots.
- Keep titles short and actionable.
- Keep descriptions concise but specific.
- severity must be one of: Low, Medium, High.
- Do not wrap the output in markdown fences.
- Do not add commentary outside JSON.
- Do not add extra keys.

Repository context:
{context_text}
""".strip()


def _build_recommendations(
    top_complex_names: list[str],
    top_incoming: list[str],
    cycles: list[Any],
    isolated_files: list[Any],
    top_outgoing: list[str],
) -> list[dict[str, str]]:
    recommendations: list[dict[str, str]] = []

    if top_complex_names:
        recommendations.append(
            {
                "title": "Split complex modules",
                "description": f"Refactor {top_complex_names[0]} into smaller responsibilities.",
            }
        )

    if top_incoming:
        recommendations.append(
            {
                "title": "Protect central modules",
                "description": f"Review {top_incoming[0]} carefully because many files depend on it.",
            }
        )

    if cycles:
        recommendations.append(
            {
                "title": "Remove circular dependencies",
                "description": "Break dependency cycles to simplify maintenance and testing.",
            }
        )

    if isolated_files:
        recommendations.append(
            {
                "title": "Review isolated files",
                "description": "Check whether isolated files are unused or should be connected to the main flow.",
            }
        )

    if top_outgoing:
        recommendations.append(
            {
                "title": "Reduce outgoing coupling",
                "description": f"Reduce the number of direct dependencies used by {top_outgoing[0]}.",
            }
        )

    while len(recommendations) < MAX_RECOMMENDATIONS:
        recommendations.append(
            {
                "title": "Improve modularity",
                "description": "Move shared logic into smaller reusable helpers and services.",
            }
        )

    return recommendations[:MAX_RECOMMENDATIONS]


def _build_hotspots(
    top_complex_names: list[str],
    top_incoming: list[str],
    top_outgoing: list[str],
    files: list[dict[str, Any]],
) -> list[dict[str, str]]:
    hotspots: list[dict[str, str]] = []
    ranked_hotspots = _dedupe_keep_order(top_complex_names + top_incoming + top_outgoing)[
        :MAX_HOTSPOTS
    ]

    severity_map = [HIGH_SEVERITY, MEDIUM_SEVERITY, MEDIUM_SEVERITY]

    for idx, file_name in enumerate(ranked_hotspots):
        reason = "High complexity and central usage in the dependency graph."
        if file_name in top_complex_names and file_name in top_incoming:
            reason = "High complexity and many incoming dependencies."
        elif file_name in top_complex_names:
            reason = "High complexity and likely multiple responsibilities."
        elif file_name in top_incoming:
            reason = "Many files depend on this module, so changes here have wide impact."
        elif file_name in top_outgoing:
            reason = "This module depends on many others, which increases coupling."

        hotspots.append(
            {
                "file": file_name,
                "reason": reason,
                "severity": severity_map[idx],
            }
        )

    while len(hotspots) < MAX_HOTSPOTS:
        hotspots.append(
            {
                "file": str(files[0].get("path", "unknown")) if files else "unknown",
                "reason": "Useful candidate for review based on current repository structure.",
                "severity": LOW_SEVERITY if len(hotspots) == 2 else MEDIUM_SEVERITY,
            }
        )

    return hotspots[:MAX_HOTSPOTS]


def _compute_score(
    complexity: int,
    cycles: list[Any],
    top_complex_names: list[str],
    isolated_files: list[Any],
) -> int:
    score = MAX_SCORE
    score -= min(25, complexity // COMPLEXITY_PENALTY_DIVISOR)
    score -= min(15, len(cycles) * CYCLE_PENALTY_PER_ITEM)
    score -= min(10, len(top_complex_names) * TOP_COMPLEX_PENALTY_PER_ITEM)
    score -= min(10, len(isolated_files) * ISOLATED_FILE_PENALTY_PER_ITEM)
    return max(MIN_SCORE, min(MAX_SCORE, score))


def _score_to_labels(score: int) -> tuple[str, str]:
    if score >= HIGH_SCORE_THRESHOLD:
        return "High", "Excellent"
    if score >= MODERATE_SCORE_THRESHOLD:
        return "Moderate", "Good"
    return "Needs Improvement", "Average"


def _complexity_label(avg_complexity: float) -> str:
    if avg_complexity <= 3:
        return "Low"
    if avg_complexity <= 8:
        return "Moderate"
    return "High"


def _local_repository_ai(context: dict[str, Any]) -> dict[str, Any]:
    stats = context.get("stats", {}) or {}
    graph_insights = context.get("graph_insights", {}) or {}
    files = context.get("files", []) or []

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

    recommendations = _build_recommendations(
        top_complex_names=top_complex_names,
        top_incoming=top_incoming,
        cycles=cycles,
        isolated_files=isolated_files,
        top_outgoing=top_outgoing,
    )

    hotspots = _build_hotspots(
        top_complex_names=top_complex_names,
        top_incoming=top_incoming,
        top_outgoing=top_outgoing,
        files=files,
    )

    total_files = int(context.get("total_files", len(files)))
    complexity = int(stats.get("total_complexity", 0))
    avg_complexity = float(stats.get("average_complexity", 0.0))

    score = _compute_score(
        complexity=complexity,
        cycles=cycles,
        top_complex_names=top_complex_names,
        isolated_files=isolated_files,
    )

    maintainability, architecture = _score_to_labels(score)
    complexity_label = _complexity_label(avg_complexity)

    summary = (
        f"The repository contains {total_files} files and shows a reasonably modular structure. "
        f"Core pressure appears in {top_complex_names[0] if top_complex_names else 'the main analysis pipeline'}. "
        f"Focus on reducing coupling, simplifying complex modules, and protecting central files from becoming bottlenecks."
    )

    return {
        "health": {
            "score": score,
            "maintainability": maintainability,
            "architecture": architecture,
            "complexity": complexity_label,
            "summary": summary,
        },
        "recommendations": recommendations,
        "hotspots": hotspots,
    }


def _normalize_payload(
    data: dict[str, Any] | None,
    context: dict[str, Any],
) -> dict[str, Any]:
    fallback = _local_repository_ai(context)

    if not isinstance(data, dict):
        return fallback

    health = data.get("health", {})
    if not isinstance(health, dict):
        health = {}

    score = health.get("score", fallback["health"]["score"])
    try:
        score = int(score)
    except Exception:
        score = fallback["health"]["score"]

    score = max(0, min(100, score))

    def as_list_of_dicts(value: Any) -> list[dict[str, str]]:
        if not isinstance(value, list):
            return []
        result: list[dict[str, str]] = []
        for item in value:
            if not isinstance(item, dict):
                continue
            result.append(
                {
                    "title": str(item.get("title", "")).strip(),
                    "description": str(item.get("description", "")).strip(),
                }
            )
        return result

    def as_hotspots(value: Any) -> list[dict[str, str]]:
        if not isinstance(value, list):
            return []
        result: list[dict[str, str]] = []
        for item in value:
            if not isinstance(item, dict):
                continue
            result.append(
                {
                    "file": str(item.get("file", "")).strip(),
                    "reason": str(item.get("reason", "")).strip(),
                    "severity": str(item.get("severity", MEDIUM_SEVERITY)).strip()
                    or MEDIUM_SEVERITY,
                }
            )
        return result

    recommendations = as_list_of_dicts(data.get("recommendations")) or fallback["recommendations"]
    hotspots = as_hotspots(data.get("hotspots")) or fallback["hotspots"]

    maintainability = str(health.get("maintainability") or fallback["health"]["maintainability"])
    architecture = str(health.get("architecture") or fallback["health"]["architecture"])
    complexity = str(health.get("complexity") or fallback["health"]["complexity"])
    summary = str(health.get("summary") or fallback["health"]["summary"])

    if not recommendations:
        recommendations = fallback["recommendations"]
    if not hotspots:
        hotspots = fallback["hotspots"]

    return {
        "health": {
            "score": score,
            "maintainability": maintainability,
            "architecture": architecture,
            "complexity": complexity,
            "summary": summary,
        },
        "recommendations": recommendations[:MAX_RECOMMENDATIONS],
        "hotspots": hotspots[:MAX_HOTSPOTS],
    }


def _generate_with_google_sdk(prompt: str, api_key: str) -> str:
    client = google_genai.Client(api_key=api_key)
    response = client.models.generate_content(
        model=DEFAULT_MODEL_NAME,
        contents=prompt,
    )
    return getattr(response, "text", "") or ""


def _generate_with_legacy_sdk(prompt: str, api_key: str) -> str:
    legacy_genai.configure(api_key=api_key)
    model = legacy_genai.GenerativeModel(DEFAULT_MODEL_NAME)
    response = model.generate_content(prompt)
    return getattr(response, "text", "") or ""


def generate_repository_ai(context: dict[str, Any]) -> dict[str, Any]:
    """
    Returns repository intelligence:
    - health score
    - recommendations
    - hotspots

    Tries Google GenAI first, then legacy Gemini SDK, then local heuristics.
    Uses a local cache keyed by the input context.
    """
    cache_key = _cache_key_for_context(context)
    cached = _read_cache(cache_key)
    if cached:
        return cached

    prompt = build_repository_ai_prompt(context)
    fallback = _local_repository_ai(context)

    settings = get_settings()
    if not settings.gemini_api_key:
        return _cache_and_return(cache_key, fallback)

    try:
        logger.info("Using Gemini for repository AI")

        text = ""
        if google_genai is not None:
            text = _generate_with_google_sdk(prompt, settings.gemini_api_key)
        elif legacy_genai is not None:
            text = _generate_with_legacy_sdk(prompt, settings.gemini_api_key)
        else:
            return _cache_and_return(cache_key, fallback)

        if not text.strip():
            logger.info("Repository AI Gemini returned an empty response")
            return _cache_and_return(cache_key, fallback)

        parsed = _extract_json_payload(text)
        normalized = _normalize_payload(parsed, context)
        return _cache_and_return(cache_key, normalized)

    except Exception as exc:
        logger.exception("Repository AI Gemini error: %r", exc)
        return _cache_and_return(cache_key, fallback)