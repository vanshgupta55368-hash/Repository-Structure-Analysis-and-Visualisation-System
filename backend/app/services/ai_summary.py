from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.core.cache import get_cached_summary, set_cached_summary
from app.parsers.cpp_parser import cpp_parser
from app.parsers.python_parser import python_parser
from app.utils.file_utils import read_file
from app.utils.hashing import hash_text

try:
    import google.generativeai as genai  # type: ignore
except Exception:  # pragma: no cover
    genai = None


DEFAULT_MODEL_NAME = "gemini-1.5-flash"


@dataclass(frozen=True)
class SummaryContext:
    file_path: Optional[str]
    language: str
    code: str
    function_count: int = 0
    class_count: int = 0
    import_count: int = 0


def truncate_text(text: str, max_chars: int = 6000) -> str:
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1200] + "\n\n[TRUNCATED FOR PROMPT SIZE]\n"


def detect_language_from_path(file_path: str | Path | None) -> str:
    if not file_path:
        return "unknown"

    suffix = Path(file_path).suffix.lower()
    if suffix == ".py":
        return "python"
    if suffix in {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp"}:
        return "cpp"
    return "unknown"


def build_summary_context(code: str, language: str, file_path: str | None = None) -> SummaryContext:
    if language == "python":
        symbols = python_parser.extract_symbols(code)
        function_count = len(symbols.get("functions", []))
        class_count = len(symbols.get("classes", []))
        import_count = len(symbols.get("imports", []))
        return SummaryContext(
            file_path=file_path,
            language=language,
            code=code,
            function_count=function_count,
            class_count=class_count,
            import_count=import_count,
        )

    if language == "cpp":
        symbols = cpp_parser.extract_symbols(code)
        import_count = len(symbols.get("imports", []))
        return SummaryContext(
            file_path=file_path,
            language=language,
            code=code,
            function_count=0,
            class_count=0,
            import_count=import_count,
        )

    return SummaryContext(
        file_path=file_path,
        language=language,
        code=code,
        function_count=0,
        class_count=0,
        import_count=0,
    )


def build_summary_prompt(code: str, language: str, file_path: str | None = None) -> str:
    ctx = build_summary_context(code, language, file_path)
    preview = truncate_text(ctx.code, 5000)

    return f"""
You are an expert software engineer helping explain source code in a professional code review tool.

File path: {ctx.file_path or "unknown"}
Language: {ctx.language}

Your task:
1. Explain what this file does.
2. Mention important functions, classes, imports, and responsibilities.
3. Keep the explanation concise but informative.
4. Use simple language that a student can understand.
5. If the file is large or complicated, summarize it in bullet points.

Static metadata:
- Function count: {ctx.function_count}
- Class count: {ctx.class_count}
- Import count: {ctx.import_count}

Source code:
{preview}

Return only the explanation. Do not mention that you are an AI.
""".strip()


def _local_fallback_summary(code: str, language: str, file_path: str | None = None) -> str:
    ctx = build_summary_context(code, language, file_path)

    lines = code.splitlines()
    total_lines = len(lines)

    non_empty = [line for line in lines if line.strip()]
    comment_like = 0

    if language == "python":
        comment_like = sum(1 for line in lines if line.lstrip().startswith("#"))
    elif language == "cpp":
        comment_like = sum(
            1
            for line in lines
            if line.strip().startswith("//") or line.strip().startswith("/*") or line.strip().startswith("*")
        )

    imports = []
    if language == "python":
        imports = python_parser.extract_dependencies(code)
    elif language == "cpp":
        imports = cpp_parser.extract_dependencies(code)

    first_non_empty = next((line.strip() for line in lines if line.strip()), "")
    summary_parts = []

    name = Path(file_path).name if file_path else "This file"

    summary_parts.append(
        f"{name} contains {total_lines} lines, with {len(non_empty)} non-empty lines and {comment_like} comment-like lines."
    )

    if ctx.function_count or ctx.class_count:
        pieces = []
        if ctx.function_count:
            pieces.append(f"{ctx.function_count} function{'s' if ctx.function_count != 1 else ''}")
        if ctx.class_count:
            pieces.append(f"{ctx.class_count} class{'es' if ctx.class_count != 1 else ''}")
        summary_parts.append(
            f"It defines {', '.join(pieces)}."
        )

    if imports:
        preview_imports = ", ".join(imports[:5])
        summary_parts.append(f"It depends on: {preview_imports}.")

    if first_non_empty:
        summary_parts.append(f"The file starts with: `{first_non_empty[:120]}`")

    summary_parts.append(
        "Overall, this file appears to be part of the repository's implementation layer."
    )

    return " ".join(summary_parts)


def summarize_with_gemini(code: str, language: str, file_path: str | None = None) -> str:
    """
    Uses Gemini if available. Falls back cleanly when API key or SDK is absent.
    """
    prompt = build_summary_prompt(code, language, file_path)

    if genai is None:
        return _local_fallback_summary(code, language, file_path)

    from app.core.config import get_settings

    settings = get_settings()
    if not settings.gemini_api_key:
        return _local_fallback_summary(code, language, file_path)

    try:
        genai.configure(api_key=settings.gemini_api_key)
        model = genai.GenerativeModel(DEFAULT_MODEL_NAME)
        response = model.generate_content(prompt)
        text = getattr(response, "text", None)
        if text and text.strip():
            return text.strip()
    except Exception:
        pass

    return _local_fallback_summary(code, language, file_path)


def get_cached_or_generate_summary(
    file_hash: str,
    code: str,
    language: str,
    file_path: str | None = None,
) -> str:
    cached = get_cached_summary(file_hash)
    if cached:
        return cached

    summary = summarize_with_gemini(code, language, file_path)
    set_cached_summary(file_hash, summary)
    return summary


def summarize_file(
    code: str,
    language: str,
    file_path: str | None = None,
    use_cache_key: str | None = None,
) -> str:
    """
    Main public API for file summaries.
    """
    key = use_cache_key or hash_text(f"{language}::{file_path or ''}::{code}")
    return get_cached_or_generate_summary(key, code, language, file_path)


def summarize_repository(files: list[dict]) -> str:
    """
    Repository-level natural language summary.
    Accepts a list of file-like dictionaries to keep it flexible.
    """
    if not files:
        return "The repository is empty."

    languages: dict[str, int] = {}
    names: list[str] = []

    for f in files:
        lang = str(f.get("language", "unknown"))
        languages[lang] = languages.get(lang, 0) + 1
        names.append(str(f.get("name", "unknown")))

    top_names = ", ".join(names[:10])
    lang_summary = ", ".join(f"{k}: {v}" for k, v in sorted(languages.items(), key=lambda x: (-x[1], x[0])))

    return (
        f"This repository contains {len(files)} files. "
        f"Language distribution: {lang_summary}. "
        f"Representative files include: {top_names}."
    )