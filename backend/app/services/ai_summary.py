from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.core.cache import get_cached_summary, set_cached_summary
from app.parsers.cpp_parser import cpp_parser
from app.parsers.python_parser import python_parser
from app.utils.hashing import hash_text

try:
    from google import genai  # type: ignore
except Exception:  # pragma: no cover
    genai = None


logger = logging.getLogger(__name__)

DEFAULT_MODEL_NAME = "gemini-3.5-flash"

UNKNOWN_LANGUAGE = "unknown"

MAX_PROMPT_CHARS = 5000
MAX_TRUNCATE_CHARS = 6000
TRUNCATION_NOTICE = "\n\n[TRUNCATED FOR PROMPT SIZE]\n"

PARSERS = {
    "python": python_parser,
    "cpp": cpp_parser,
}


@dataclass(frozen=True)
class SummaryContext:
    file_path: Optional[str]
    language: str
    code: str
    function_count: int = 0
    class_count: int = 0
    import_count: int = 0


def truncate_text(text: str, max_chars: int = MAX_TRUNCATE_CHARS) -> str:
    """
    Truncate source code to fit within the LLM prompt budget.
    """
    if len(text) <= max_chars:
        return text

    reserved = len(TRUNCATION_NOTICE)
    return text[: max_chars - reserved] + TRUNCATION_NOTICE


def detect_language_from_path(file_path: str | Path | None) -> str:
    """
    Infer the source language from a file extension.
    """
    if not file_path:
        return UNKNOWN_LANGUAGE

    suffix = Path(file_path).suffix.lower()

    if suffix == ".py":
        return "python"

    if suffix in {
        ".c",
        ".cc",
        ".cpp",
        ".cxx",
        ".h",
        ".hh",
        ".hpp",
    }:
        return "cpp"

    return UNKNOWN_LANGUAGE


def build_summary_context(
    code: str,
    language: str,
    file_path: str | None = None,
) -> SummaryContext:
    """
    Build metadata used by both the Gemini prompt and
    the local fallback summarizer.
    """
    parser = PARSERS.get(language)

    function_count = 0
    class_count = 0
    import_count = 0

    if parser is not None:
        symbols = parser.extract_symbols(code)

        function_count = len(symbols.get("functions", []))
        import_count = len(symbols.get("imports", []))

        if language == "python":
            class_count = len(symbols.get("classes", []))

    return SummaryContext(
        file_path=file_path,
        language=language,
        code=code,
        function_count=function_count,
        class_count=class_count,
        import_count=import_count,
    )


def build_summary_prompt(
    code: str,
    language: str,
    file_path: str | None = None,
) -> str:
    """
    Construct the prompt sent to Gemini.
    """
    context = build_summary_context(
        code=code,
        language=language,
        file_path=file_path,
    )

    preview = truncate_text(
        context.code,
        MAX_PROMPT_CHARS,
    )

    return f"""
You are an expert software engineer helping explain source code in a professional code review tool.

File path: {context.file_path or "unknown"}
Language: {context.language}

Your task:

1. Explain what this file does.
2. Mention important functions, classes, imports, and responsibilities.
3. Keep the explanation concise but informative.
4. Use simple language that a student can understand.
5. If the file is large or complicated, summarize it in bullet points.

Static metadata:

- Function count: {context.function_count}
- Class count: {context.class_count}
- Import count: {context.import_count}

Source code:

{preview}

Return only the explanation.
Do not mention that you are an AI.
""".strip()
def _extract_dependencies(code: str, language: str) -> list[str]:
    """
    Extract language-specific dependencies.
    """
    parser = PARSERS.get(language)
    if parser is None:
        return []

    return parser.extract_dependencies(code)


def _local_fallback_summary(
    code: str,
    language: str,
    file_path: str | None = None,
) -> str:
    """
    Generate a deterministic summary without using Gemini.
    """
    context = build_summary_context(
        code=code,
        language=language,
        file_path=file_path,
    )

    lines = code.splitlines()
    total_lines = len(lines)

    non_empty_lines = [line for line in lines if line.strip()]

    if language == "python":
        comment_lines = sum(
            1
            for line in lines
            if line.lstrip().startswith("#")
        )
    elif language == "cpp":
        comment_lines = sum(
            1
            for line in lines
            if (
                line.strip().startswith("//")
                or line.strip().startswith("/*")
                or line.strip().startswith("*")
            )
        )
    else:
        comment_lines = 0

    imports = _extract_dependencies(code, language)

    first_non_empty = next(
        (line.strip() for line in lines if line.strip()),
        "",
    )

    summary_parts: list[str] = []

    filename = (
        Path(file_path).name
        if file_path
        else "This file"
    )

    summary_parts.append(
        f"{filename} contains {total_lines} lines, "
        f"with {len(non_empty_lines)} non-empty lines "
        f"and {comment_lines} comment-like lines."
    )

    if context.function_count or context.class_count:
        definitions: list[str] = []

        if context.function_count:
            definitions.append(
                f"{context.function_count} function"
                f"{'s' if context.function_count != 1 else ''}"
            )

        if context.class_count:
            definitions.append(
                f"{context.class_count} class"
                f"{'es' if context.class_count != 1 else ''}"
            )

        summary_parts.append(
            f"It defines {', '.join(definitions)}."
        )

    if imports:
        summary_parts.append(
            f"It depends on: {', '.join(imports[:5])}."
        )

    if first_non_empty:
        summary_parts.append(
            f"The file starts with: `{first_non_empty[:120]}`"
        )

    summary_parts.append(
        "Overall, this file appears to be part of the repository's implementation layer."
    )

    return " ".join(summary_parts)


def summarize_with_gemini(
    code: str,
    language: str,
    file_path: str | None = None,
) -> str:
    """
    Generate a natural-language summary using Gemini.

    Falls back to a deterministic local summary when:
    - Gemini SDK is unavailable
    - API key is missing
    - Gemini returns an empty response
    - Gemini raises an exception
    """
    prompt = build_summary_prompt(
        code=code,
        language=language,
        file_path=file_path,
    )

    fallback = _local_fallback_summary(
        code=code,
        language=language,
        file_path=file_path,
    )

    if genai is None:
        logger.info("Gemini SDK not installed. Using local summary.")
        return fallback

    from app.core.config import get_settings

    settings = get_settings()

    if not settings.gemini_api_key:
        logger.info("Gemini API key not configured. Using local summary.")
        return fallback

    try:
        logger.info("Generating summary using Gemini...")

        client = genai.Client(
            api_key=settings.gemini_api_key,
        )

        response = client.models.generate_content(
            model=DEFAULT_MODEL_NAME,
            contents=prompt,
        )

        text = getattr(response, "text", None)

        if text and text.strip():
            logger.info("Gemini summary generated successfully.")
            return text.strip()

        logger.warning(
            "Gemini returned an empty response. Falling back to local summary."
        )

    except Exception:
        logger.exception(
            "Gemini summary generation failed."
        )

    return fallback
def get_cached_or_generate_summary(
    file_hash: str,
    code: str,
    language: str,
    file_path: str | None = None,
) -> str:
    """
    Retrieve a cached summary or generate one if it does not exist.
    """
    cached_summary = get_cached_summary(file_hash)
    if cached_summary is not None:
        return cached_summary

    summary = summarize_with_gemini(
        code=code,
        language=language,
        file_path=file_path,
    )

    set_cached_summary(file_hash, summary)
    return summary


def summarize_file(
    code: str,
    language: str,
    file_path: str | None = None,
    use_cache_key: str | None = None,
) -> str:
    """
    Public API for generating a file summary.

    A caller may provide a cache key. Otherwise one is generated from
    the language, file path and file contents.
    """
    cache_key = use_cache_key or hash_text(
        f"{language}::{file_path or ''}::{code}"
    )

    return get_cached_or_generate_summary(
        file_hash=cache_key,
        code=code,
        language=language,
        file_path=file_path,
    )


def summarize_repository(files: list[dict]) -> str:
    """
    Generate a lightweight natural-language summary of a repository.
    """
    if not files:
        return "The repository is empty."

    language_counts: dict[str, int] = {}
    representative_files: list[str] = []

    for file in files:
        language = str(file.get("language", UNKNOWN_LANGUAGE))
        language_counts[language] = (
            language_counts.get(language, 0) + 1
        )

        representative_files.append(
            str(file.get("name", "unknown"))
        )

    language_summary = ", ".join(
        f"{language}: {count}"
        for language, count in sorted(
            language_counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )

    representative_summary = ", ".join(
        representative_files[:10]
    )

    return (
        f"This repository contains {len(files)} files. "
        f"Language distribution: {language_summary}. "
        f"Representative files include: {representative_summary}."
    )