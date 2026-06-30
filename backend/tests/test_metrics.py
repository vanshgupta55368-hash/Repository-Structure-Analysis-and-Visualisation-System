from __future__ import annotations

from app.services.metrics import (
    count_blank_lines,
    count_comment_lines,
    count_lines,
    estimate_complexity,
)


def test_basic_line_metrics():
    code = "a = 1\n\n# comment\nif a:\n    print(a)\n"
    assert count_lines(code) == 5
    assert count_blank_lines(code) == 1
    assert count_comment_lines(code, "python") == 1


def test_python_complexity():
    code = """
def f(x):
    if x > 0:
        for i in range(x):
            if i % 2 == 0:
                print(i)
"""
    complexity = estimate_complexity(code, "python")
    assert complexity >= 4