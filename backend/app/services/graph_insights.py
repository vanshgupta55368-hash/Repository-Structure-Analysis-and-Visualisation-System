from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

from app.models.file_model import FileNode
from app.models.graph_model import GraphEdge
from app.schemas import GraphInsightsSchema


AdjacencyMap = dict[str, set[str]]

WHITE = 0
GRAY = 1
BLACK = 2


def build_adjacency(
    files: list[FileNode],
    edges: list[GraphEdge],
) -> tuple[AdjacencyMap, AdjacencyMap]:
    """Build outgoing and incoming adjacency maps."""
    outgoing: AdjacencyMap = defaultdict(set)
    incoming: AdjacencyMap = defaultdict(set)

    file_ids = {file.id for file in files}

    # Ensure every file exists in both maps.
    for file_id in file_ids:
        outgoing[file_id]
        incoming[file_id]

    for edge in edges:
        if edge.source not in file_ids or edge.target not in file_ids:
            continue

        outgoing[edge.source].add(edge.target)
        incoming[edge.target].add(edge.source)

    return outgoing, incoming


def detect_isolated_files(
    files: list[FileNode],
    outgoing: AdjacencyMap,
    incoming: AdjacencyMap,
) -> list[str]:
    """Return files with no incoming or outgoing edges."""
    return sorted(
        file.id
        for file in files
        if not outgoing[file.id] and not incoming[file.id]
    )


def top_degree_files(
    degree_map: AdjacencyMap,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Return the nodes with the highest degree."""
    ranked = sorted(
        degree_map.items(),
        key=lambda item: (-len(item[1]), item[0]),
    )

    return [
        {
            "file": file_id,
            "count": len(neighbors),
        }
        for file_id, neighbors in ranked[:limit]
    ]


def connected_components(
    files: list[FileNode],
    outgoing: AdjacencyMap,
    incoming: AdjacencyMap,
) -> list[list[str]]:
    """Compute connected components treating the graph as undirected."""
    all_neighbors: AdjacencyMap = defaultdict(set)

    for file_id, neighbors in outgoing.items():
        all_neighbors[file_id].update(neighbors)

    for file_id, neighbors in incoming.items():
        all_neighbors[file_id].update(neighbors)

    visited: set[str] = set()
    components: list[list[str]] = []

    for file in files:
        if file.id in visited:
            continue

        queue = deque([file.id])
        component: list[str] = []

        while queue:
            node = queue.popleft()

            if node in visited:
                continue

            visited.add(node)
            component.append(node)

            for neighbor in all_neighbors[node]:
                if neighbor not in visited:
                    queue.append(neighbor)

        components.append(sorted(component))

    components.sort(
        key=lambda component: (
            -len(component),
            component[0] if component else "",
        )
    )

    return components


def detect_cycles(outgoing: AdjacencyMap) -> list[list[str]]:
    """Detect cycles using depth-first search."""
    color: dict[str, int] = {
        node: WHITE
        for node in outgoing
    }

    parent: dict[str, str | None] = {
        node: None
        for node in outgoing
    }

    cycles: list[list[str]] = []

    def reconstruct_cycle(start: str, end: str) -> list[str]:
        cycle = [end]
        current = start

        while current is not None and current != end:
            cycle.append(current)
            current = parent[current]

        cycle.append(end)
        cycle.reverse()
        return cycle

    def dfs(node: str) -> None:
        color[node] = GRAY

        for neighbor in outgoing[node]:
            if color[neighbor] == WHITE:
                parent[neighbor] = node
                dfs(neighbor)
            elif color[neighbor] == GRAY:
                cycles.append(reconstruct_cycle(node, neighbor))

        color[node] = BLACK

    for node in outgoing:
        if color[node] == WHITE:
            dfs(node)

    unique_cycles: list[list[str]] = []
    seen: set[tuple[str, ...]] = set()

    for cycle in cycles:
        signature = tuple(cycle)
        if signature in seen:
            continue

        seen.add(signature)
        unique_cycles.append(cycle)

    return unique_cycles


def analyze_graph(
    files: list[FileNode],
    edges: list[GraphEdge],
) -> GraphInsightsSchema:
    """Generate graph insights from repository dependency data."""
    outgoing, incoming = build_adjacency(files, edges)

    return GraphInsightsSchema(
        isolated_files=detect_isolated_files(
            files,
            outgoing,
            incoming,
        ),
        top_incoming=top_degree_files(
            incoming,
            limit=10,
        ),
        top_outgoing=top_degree_files(
            outgoing,
            limit=10,
        ),
        connected_components=connected_components(
            files,
            outgoing,
            incoming,
        ),
        cycles=detect_cycles(outgoing),
    )