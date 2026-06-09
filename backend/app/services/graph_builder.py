from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from app.models.file_model import FileNode
from app.models.graph_model import GraphEdge, GraphNode, GraphResponse
from app.models.metrics_model import FileMetrics


def _build_dependency_index(files: list[FileNode]) -> dict[str, FileNode]:
    index: dict[str, FileNode] = {}

    for file in files:
        rel_no_ext = Path(file.path).with_suffix("")
        parts = rel_no_ext.parts
        stem = Path(file.name).stem

        keys = {
            file.id,
            file.path,
            file.name,
            stem,
            "/".join(parts),
            ".".join(parts),
        }

        for key in keys:
            if key:
                index[key] = file

    return index


def _dependency_to_candidates(dep: str) -> list[str]:
    cleaned = dep.strip().lstrip(".")
    if not cleaned:
        return []

    candidates = [cleaned]
    candidates.append(cleaned.replace(".", "/"))
    candidates.append(cleaned.replace(".", "/") + ".py")
    candidates.append(cleaned + ".py")
    candidates.append(cleaned + "/__init__.py")
    candidates.append(cleaned.replace(".", "/") + "/__init__.py")

    if "/" in cleaned:
        candidates.append(cleaned.split("/")[-1])
        candidates.append(cleaned.split("/")[-1] + ".py")

    return list(dict.fromkeys(candidates))


def resolve_dependency(dep: str, file_index: dict[str, FileNode]) -> FileNode | None:
    for candidate in _dependency_to_candidates(dep):
        if candidate in file_index:
            return file_index[candidate]
    return None


def build_nodes(
    files: list[FileNode],
    metrics_by_file: dict[str, FileMetrics] | None = None,
) -> list[GraphNode]:
    nodes: list[GraphNode] = []

    for file in files:
        metrics = None
        if metrics_by_file:
            metrics = metrics_by_file.get(file.id) or metrics_by_file.get(file.path)

        label = file.name
        if metrics:
            label = f"{file.name} ({metrics.loc} LOC)"

        nodes.append(
            GraphNode(
                id=file.id,
                label=label,
            )
        )

    return nodes


def build_edges(
    files: list[FileNode],
    dependency_map: dict[str, list[str]],
) -> list[GraphEdge]:
    file_index = _build_dependency_index(files)
    edges: list[GraphEdge] = []
    seen: set[tuple[str, str, str]] = set()

    for source_file, deps in dependency_map.items():
        source = file_index.get(source_file)
        if source is None:
            continue

        for dep in deps:
            target = resolve_dependency(dep, file_index)
            if target is None:
                continue
            if target.id == source.id:
                continue

            edge_key = (source.id, target.id, "import")
            if edge_key in seen:
                continue

            seen.add(edge_key)
            edges.append(
                GraphEdge(
                    source=source.id,
                    target=target.id,
                    relation="import",
                )
            )

    return edges


def build_graph(
    files: list[FileNode],
    dependency_map: dict[str, list[str]],
    metrics_by_file: dict[str, FileMetrics] | None = None,
) -> GraphResponse:
    nodes = build_nodes(files, metrics_by_file)
    edges = build_edges(files, dependency_map)
    return GraphResponse(nodes=nodes, edges=edges)