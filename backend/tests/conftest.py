from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture()
def sample_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "sample_repo"
    repo.mkdir()

    (repo / ".git").mkdir()
    (repo / "__pycache__").mkdir()

    (repo / "main.py").write_text(
        "import os\nfrom utils import helper\n\n\ndef main():\n    if True:\n        helper()\n",
        encoding="utf-8",
    )
    (repo / "utils.py").write_text(
        "def helper():\n    return 42\n",
        encoding="utf-8",
    )
    (repo / "models.py").write_text(
        "class User:\n    pass\n",
        encoding="utf-8",
    )
    (repo / "binary.bin").write_bytes(b"\x00\x01\x02")

    cache_dir = repo / ".git" / "config"
    cache_dir.write_text("ignore", encoding="utf-8")

    return repo