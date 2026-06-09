from __future__ import annotations

import ast
from typing import Any

from app.parsers.base import BaseParser, unique_sorted


class _PythonAnalyzer(ast.NodeVisitor):
    def __init__(self) -> None:
        self.imports: set[str] = set()
        self.functions: set[str] = set()
        self.classes: set[str] = set()

    def visit_Import(self, node: ast.Import) -> Any:
        for alias in node.names:
            name = alias.name.strip()
            if name:
                self.imports.add(name)
                self.imports.add(name.split(".")[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> Any:
        module = node.module or ""
        prefix = "." * node.level
        combined = f"{prefix}{module}".strip(".")
        if combined:
            self.imports.add(combined)
            self.imports.add(combined.split(".")[0])
        for alias in node.names:
            if alias.name != "*":
                self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        self.functions.add(node.name)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:
        self.functions.add(node.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> Any:
        self.classes.add(node.name)
        self.generic_visit(node)


class PythonParser(BaseParser):
    supported_extensions = {".py"}

    def extract_dependencies(self, code: str, file_path: str | None = None) -> list[str]:
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []

        analyzer = _PythonAnalyzer()
        analyzer.visit(tree)
        return unique_sorted(analyzer.imports)

    def extract_symbols(self, code: str) -> dict[str, list[str]]:
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"functions": [], "classes": [], "imports": []}

        analyzer = _PythonAnalyzer()
        analyzer.visit(tree)
        return {
            "functions": unique_sorted(analyzer.functions),
            "classes": unique_sorted(analyzer.classes),
            "imports": unique_sorted(analyzer.imports),
        }


python_parser = PythonParser()