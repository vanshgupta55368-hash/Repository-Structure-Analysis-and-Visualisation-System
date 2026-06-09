from __future__ import annotations

import re

from app.parsers.base import BaseParser, unique_sorted

_INCLUDE_PATTERN = re.compile(
    r'^\s*#\s*include\s*(?P<bracket>[<"])(?P<header>[^>"]+)[>"]',
    re.MULTILINE,
)


class CppParser(BaseParser):
    supported_extensions = {".c", ".cc", ".cpp", ".cxx", ".h", ".hh", ".hpp"}

    def extract_includes(self, code: str) -> list[str]:
        includes: set[str] = set()
        for match in _INCLUDE_PATTERN.finditer(code):
            header = match.group("header").strip()
            if header:
                includes.add(header)
                if "/" in header:
                    includes.add(header.split("/")[-1])
        return unique_sorted(includes)

    def extract_dependencies(self, code: str, file_path: str | None = None) -> list[str]:
        return self.extract_includes(code)

    def extract_symbols(self, code: str) -> dict[str, list[str]]:
        return {
            "functions": [],
            "classes": [],
            "imports": self.extract_includes(code),
        }


cpp_parser = CppParser()