from __future__ import annotations

from app.services.ai_summary import build_summary_prompt, summarize_file


def test_build_summary_prompt_contains_metadata():
    code = "def hello():\n    return 1\n"
    prompt = build_summary_prompt(code, "python", "src/app.py")

    assert "src/app.py" in prompt
    assert "python" in prompt
    assert "function count" in prompt.lower()


def test_summarize_file_falls_back_cleanly():
    code = """
class User:
    pass

def run():
    return 1
"""
    summary = summarize_file(code, "python", "src/models.py", use_cache_key="test-key-001")

    assert isinstance(summary, str)
    assert len(summary) > 20