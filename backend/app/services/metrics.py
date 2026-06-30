from __future__ import annotations

import ast
from pathlib import Path

from app.models.metrics_model import FileMetrics
from app.parsers.cpp_parser import cpp_parser
from app.parsers.python_parser import python_parser
from app.utils.file_utils import read_file


_PARSERS = {
    "python": python_parser,
    "cpp": cpp_parser,
}


_CPP_COMPLEXITY_TOKENS = (
    "if",
    "for",
    "while",
    "case",
    "catch",
    "&&",
    "||",
    "?",
)


class _PythonComplexityVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.score = 1

    def visit_If(self, node: ast.If) -> None:
        self.score += 1
        self.generic_visit(node)

    def visit_For(self, node: ast.For) -> None:
        self.score += 1
        self.generic_visit(node)

    def visit_AsyncFor(self, node: ast.AsyncFor) -> None:
        self.score += 1
        self.generic_visit(node)

    def visit_While(self, node: ast.While) -> None:
        self.score += 1
        self.generic_visit(node)

    def visit_Try(self, node: ast.Try) -> None:
        self.score += 1 + len(node.handlers)
        self.generic_visit(node)

    def visit_With(self, node: ast.With) -> None:
        self.score += 1
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp) -> None:
        self.score += max(0, len(node.values) - 1)
        self.generic_visit(node)

    def visit_IfExp(self, node: ast.IfExp) -> None:
        self.score += 1
        self.generic_visit(node)

    def visit_Match(self, node: ast.Match) -> None:
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

    if language != "cpp":
        return 0

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
        score = 1
        for token in _CPP_COMPLEXITY_TOKENS:
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

    parser = _PARSERS.get(language)
    dep_count = len(parser.extract_dependencies(code)) if parser else 0

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

    metrics = list(metrics_by_file.values())

    total_loc = sum(m.loc for m in metrics)
    total_blank = sum(m.blank_lines for m in metrics)
    total_comment = sum(m.comment_lines for m in metrics)
    total_code = sum(m.code_lines for m in metrics)
    total_complexity = sum(m.complexity for m in metrics)

    average_complexity = total_complexity / len(metrics)

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
        "average_complexity": round(average_complexity, 2),
        "top_complex_files": [
            {
                "file": file_name,
                "complexity": metrics.complexity,
            }
            for file_name, metrics in top_complex_files
        ],
    }