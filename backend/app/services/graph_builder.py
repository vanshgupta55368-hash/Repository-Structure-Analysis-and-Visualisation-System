from __future__ import annotations

from pathlib import Path

from app.models.file_model import FileNode
from app.models.graph_model import GraphEdge, GraphNode, GraphResponse
from app.models.metrics_model import FileMetrics


IMPORT_RELATION = "import"


def _build_dependency_index(files: list[FileNode]) -> dict[str, FileNode]:
    """Build multiple lookup keys for dependency resolution."""
    index: dict[str, FileNode] = {}

    for file in files:
        rel_no_ext = Path(file.path).with_suffix("")
        parts = rel_no_ext.parts
        stem = Path(file.name).stem

        keys = (
            file.id,
            file.path,
            file.name,
            stem,
            "/".join(parts),
            ".".join(parts),
        )

        for key in keys:
            if key:
                index[key] = file

    return index


def _dependency_to_candidates(dep: str) -> list[str]:
    """Generate possible file/module names for a dependency."""
    cleaned = dep.strip().lstrip(".")
    if not cleaned:
        return []

    slash_path = cleaned.replace(".", "/")
    candidates = [
        cleaned,
        slash_path,
        f"{slash_path}.py",
        f"{cleaned}.py",
        f"{cleaned}/__init__.py",
        f"{slash_path}/__init__.py",
    ]

    if "/" in cleaned:
        filename = cleaned.rsplit("/", 1)[-1]
        candidates.extend(
            [
                filename,
                f"{filename}.py",
            ]
        )

    # Preserve insertion order while removing duplicates.
    return list(dict.fromkeys(candidates))


def resolve_dependency(
    dep: str,
    file_index: dict[str, FileNode],
) -> FileNode | None:
    """Resolve a dependency string to a FileNode."""
    for candidate in _dependency_to_candidates(dep):
        node = file_index.get(candidate)
        if node is not None:
            return node
    return None


def build_nodes(
    files: list[FileNode],
    metrics_by_file: dict[str, FileMetrics] | None = None,
) -> list[GraphNode]:
    nodes: list[GraphNode] = []

    for file in files:
        metrics = None
        if metrics_by_file:
            metrics = (
                metrics_by_file.get(file.id)
                or metrics_by_file.get(file.path)
            )

        label = (
            f"{file.name} ({metrics.loc} LOC)"
            if metrics
            else file.name
        )

        nodes.append(
            GraphNode(
                id=file.id,
                label=label,
                file_path=file.path,
                language=file.language,
                complexity=metrics.complexity if metrics else 0,
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

    for source_file, dependencies in dependency_map.items():
        source = file_index.get(source_file)
        if source is None:
            continue

        for dependency in dependencies:
            target = resolve_dependency(dependency, file_index)
            if target is None or target.id == source.id:
                continue

            edge_key = (
                source.id,
                target.id,
                IMPORT_RELATION,
            )

            if edge_key in seen:
                continue

            seen.add(edge_key)

            edges.append(
                GraphEdge(
                    source=source.id,
                    target=target.id,
                    relation=IMPORT_RELATION,
                )
            )

    return edges


def build_graph(
    files: list[FileNode],
    dependency_map: dict[str, list[str]],
    metrics_by_file: dict[str, FileMetrics] | None = None,
) -> GraphResponse:
    """Construct the repository dependency graph."""
    return GraphResponse(
        nodes=build_nodes(files, metrics_by_file),
        edges=build_edges(files, dependency_map),
    )