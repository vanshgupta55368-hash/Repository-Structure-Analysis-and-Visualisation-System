from __future__ import annotations

from app.models.file_model import FileNode, FileScanResult
from app.models.graph_model import GraphEdge, GraphNode, GraphResponse, GraphStats
from app.models.metrics_model import FileMetrics, RepositoryMetrics


def test_file_node_model():
    node = FileNode(
        id="main.py",
        name="main.py",
        path="main.py",
        language="python",
        extension=".py",
        size=123,
    )
    assert node.id == "main.py"
    assert node.extension == ".py"


def test_graph_response_model():
    response = GraphResponse(
        nodes=[GraphNode(id="a", label="A")],
        edges=[GraphEdge(source="a", target="b", relation="import")],
        stats=GraphStats(node_count=1, edge_count=1),
        repo_hash="xyz",
    )
    assert response.stats.node_count == 1
    assert response.repo_hash == "xyz"


def test_metrics_models():
    file_metrics = FileMetrics(loc=10, complexity=3)
    repo_metrics = RepositoryMetrics(total_files=1, total_loc=10)

    assert file_metrics.loc == 10
    assert repo_metrics.total_files == 1


def test_scan_result_model():
    result = FileScanResult(repo_path=".", total_files=1)
    assert result.repo_path == "."