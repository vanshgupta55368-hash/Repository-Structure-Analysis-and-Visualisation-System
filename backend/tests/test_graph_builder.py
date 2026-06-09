from __future__ import annotations

from app.models.file_model import FileNode
from app.services.graph_builder import build_graph


def test_graph_builder_creates_nodes_and_edges():
    files = [
        FileNode(
            id="main.py",
            name="main.py",
            path="main.py",
            language="python",
            extension=".py",
            size=100,
            file_hash="a",
        ),
        FileNode(
            id="utils.py",
            name="utils.py",
            path="utils.py",
            language="python",
            extension=".py",
            size=80,
            file_hash="b",
        ),
    ]

    dependency_map = {
        "main.py": ["utils"],
    }

    graph = build_graph(files=files, dependency_map=dependency_map)

    assert len(graph.nodes) == 2
    assert len(graph.edges) == 1
    assert graph.edges[0].source == "main.py"
    assert graph.edges[0].target == "utils.py"
    assert graph.edges[0].relation == "import"