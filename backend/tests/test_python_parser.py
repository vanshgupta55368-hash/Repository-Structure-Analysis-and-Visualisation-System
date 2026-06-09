from __future__ import annotations

from app.parsers.python_parser import python_parser


def test_python_parser_extracts_imports_functions_classes():
    code = """
import os
import numpy as np
from utils import helper
from package.core import tool

class User:
    pass

def main():
    return helper()
"""
    deps = python_parser.extract_dependencies(code)
    symbols = python_parser.extract_symbols(code)

    assert "os" in deps
    assert "numpy" in deps
    assert "utils" in deps or "helper" in deps
    assert "package" in deps or "package.core" in deps

    assert "main" in symbols["functions"]
    assert "User" in symbols["classes"]
    assert len(symbols["imports"]) >= 3