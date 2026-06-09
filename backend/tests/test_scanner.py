from __future__ import annotations

from app.services.scanner import detect_language, scan_repository, should_ignore_directory


def test_should_ignore_directory():
    assert should_ignore_directory(".git") is True
    assert should_ignore_directory("__pycache__") is True
    assert should_ignore_directory("src") is False


def test_detect_language():
    assert detect_language("file.py") == "python"
    assert detect_language("file.cpp") == "cpp"
    assert detect_language("file.txt") == "text"
    assert detect_language("file.unknown") == "unknown"


def test_scan_repository_ignores_noise(sample_repo):
    files = scan_repository(sample_repo)
    names = {f.name for f in files}

    assert "main.py" in names
    assert "utils.py" in names
    assert "models.py" in names
    assert "binary.bin" not in names
    assert "config" not in names
    assert "ignore" not in names