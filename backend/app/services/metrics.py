from __future__ import annotations

import ast
from collections import Counter
from pathlib import Path

from app.models.file_model import FileNode
from app.models.metrics_model import FileMetrics
from app.parsers.cpp_parser import cpp_parser
from app.parsers.python_parser import python_parser
from app.utils.file_utils import read_file


class _PythonComplexityVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.score = 1

    def visit_If(self, node):
        self.score += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.score += 1
        self.generic_visit(node)

    def visit_AsyncFor(self, node):
        self.score += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.score += 1
        self.generic_visit(node)

    def visit_Try(self, node):
        self.score += 1 + len(node.handlers)
        self.generic_visit(node)

    def visit_With(self, node):
        self.score += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        self.score += max(0, len(node.values) - 1)
        self.generic_visit(node)

    def visit_IfExp(self, node):
        self.score += 1
        self.generic_visit(node)

    def visit_Match(self, node):
        self.score += 1
        self.generic_visit(node)


def count_lines(code: str) -> int:
    return len(code.splitlines())


def count_blank_lines(code: str) -> int:
    return sum(1 for line in code.splitlines() if not line.strip())


def count_comment_lines(code: str, language: str) -> int:
    lines = code.splitlines()

    if language == "python":
        return sum(1 for line in lines if line.lstrip().startswith("#"))

    if language == "cpp":
        total = 0
        in_block = False
        for line in lines:
            stripped = line.strip()
            if in_block:
                total += 1
                if "*/" in stripped:
                    in_block = False
                continue
            if stripped.startswith("//"):
                total += 1
            elif stripped.startswith("/*"):
                total += 1
                if "*/" not in stripped:
                    in_block = True
        return total

    return 0


def estimate_complexity(code: str, language: str) -> int:
    if language == "python":
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return 1
        visitor = _PythonComplexityVisitor()
        visitor.visit(tree)
        return max(1, visitor.score)

    if language == "cpp":
        tokens = [
            "if",
            "for",
            "while",
            "case",
            "catch",
            "&&",
            "||",
            "?",
        ]
        score = 1
        for token in tokens:
            score += code.count(token)
        return max(1, score)

    return 1


def compute_file_metrics(file_path: str | Path, language: str) -> FileMetrics:
    code = read_file(file_path)
    loc = count_lines(code)
    blank_lines = count_blank_lines(code)
    comment_lines = count_comment_lines(code, language)
    code_lines = max(0, loc - blank_lines - comment_lines)
    complexity = estimate_complexity(code, language)

    if language == "python":
        imports = python_parser.extract_dependencies(code)
        dep_count = len(imports)
    elif language == "cpp":
        imports = cpp_parser.extract_dependencies(code)
        dep_count = len(imports)
    else:
        dep_count = 0

    return FileMetrics(
        loc=loc,
        blank_lines=blank_lines,
        comment_lines=comment_lines,
        code_lines=code_lines,
        complexity=complexity,
        num_imports=dep_count,
        num_dependencies=dep_count,
    )


def compute_repo_metrics(metrics_by_file: dict[str, FileMetrics]) -> dict[str, object]:
    if not metrics_by_file:
        return {
            "total_loc": 0,
            "total_blank_lines": 0,
            "total_comment_lines": 0,
            "total_code_lines": 0,
            "total_complexity": 0,
            "average_complexity": 0.0,
            "top_complex_files": [],
        }

    total_loc = sum(m.loc for m in metrics_by_file.values())
    total_blank = sum(m.blank_lines for m in metrics_by_file.values())
    total_comment = sum(m.comment_lines for m in metrics_by_file.values())
    total_code = sum(m.code_lines for m in metrics_by_file.values())
    total_complexity = sum(m.complexity for m in metrics_by_file.values())
    avg_complexity = total_complexity / max(1, len(metrics_by_file))

    top_complex_files = sorted(
        metrics_by_file.items(),
        key=lambda item: item[1].complexity,
        reverse=True,
    )[:5]

    return {
        "total_loc": total_loc,
        "total_blank_lines": total_blank,
        "total_comment_lines": total_comment,
        "total_code_lines": total_code,
        "total_complexity": total_complexity,
        "average_complexity": round(avg_complexity, 2),
        "top_complex_files": [
            {"file": file_id, "complexity": metrics.complexity}
            for file_id, metrics in top_complex_files
        ],
    }