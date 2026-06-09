from __future__ import annotations

IGNORED_DIRECTORIES = {
    ".git",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    "out",
    ".idea",
    ".vscode",
}

IGNORED_FILES = {
    ".DS_Store",
    "Thumbs.db",
}

SUPPORTED_LANGUAGE_EXTENSIONS = {
    ".py": "python",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".cxx": "cpp",
    ".hpp": "cpp",
    ".h": "cpp",
    ".hh": "cpp",
    ".c": "cpp",
    ".json": "json",
    ".md": "markdown",
    ".txt": "text",
}

COMMENT_PREFIXES = {
    "python": ["#"],
    "cpp": ["//", "/*", "*"],
}

MAX_FILE_SIZE_BYTES = 2_000_000
DEFAULT_ENCODING = "utf-8"