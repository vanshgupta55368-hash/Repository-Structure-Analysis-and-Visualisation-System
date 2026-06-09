from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

from app.models.file_model import FileNode
from app.models.graph_model import GraphEdge
from app.schemas import GraphInsightsSchema


def build_adjacency(
    files: list[FileNode],
    edges: list[GraphEdge],
) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    outgoing: dict[str, set[str]] = defaultdict(set)
    incoming: dict[str, set[str]] = defaultdict(set)

    file_ids = {f.id for f in files}

    for file_id in file_ids:
        outgoing[file_id]
        incoming[file_id]

    for edge in edges:
        if edge.source in file_ids and edge.target in file_ids:
            outgoing[edge.source].add(edge.target)
            incoming[edge.target].add(edge.source)

    return outgoing, incoming


def detect_isolated_files(
    files: list[FileNode],
    outgoing: dict[str, set[str]],
    incoming: dict[str, set[str]],
) -> list[str]:
    isolated = []
    for f in files:
        if not outgoing[f.id] and not incoming[f.id]:
            isolated.append(f.id)
    return sorted(isolated)


def top_degree_files(
    degree_map: dict[str, set[str]],
    limit: int = 10,
) -> list[dict[str, Any]]:
    ranked = sorted(
        degree_map.items(),
        key=lambda item: (-len(item[1]), item[0]),
    )
    return [
        {"file": file_id, "count": len(neighbors)}
        for file_id, neighbors in ranked[:limit]
    ]


def connected_components(
    files: list[FileNode],
    outgoing: dict[str, set[str]],
    incoming: dict[str, set[str]],
) -> list[list[str]]:
    all_neighbors: dict[str, set[str]] = defaultdict(set)

    for file_id in outgoing:
        all_neighbors[file_id].update(outgoing[file_id])
    for file_id in incoming:
        all_neighbors[file_id].update(incoming[file_id])

    visited: set[str] = set()
    components: list[list[str]] = []

    for f in files:
        if f.id in visited:
            continue

        queue = deque([f.id])
        component: list[str] = []

        while queue:
            node = queue.popleft()
            if node in visited:
                continue

            visited.add(node)
            component.append(node)

            for nxt in all_neighbors[node]:
                if nxt not in visited:
                    queue.append(nxt)

        components.append(sorted(component))

    components.sort(key=lambda comp: (-len(comp), comp[0] if comp else ""))
    return components


def detect_cycles(outgoing: dict[str, set[str]]) -> list[list[str]]:
    WHITE, GRAY, BLACK = 0, 1, 2
    color: dict[str, int] = {node: WHITE for node in outgoing}
    parent: dict[str, str | None] = {node: None for node in outgoing}
    cycles: list[list[str]] = []

    def reconstruct_cycle(start: str, end: str) -> list[str]:
        cycle = [end]
        cur = start
        while cur is not None and cur != end:
            cycle.append(cur)
            cur = parent[cur]
        cycle.append(end)
        cycle.reverse()
        return cycle

    def dfs(u: str) -> None:
        color[u] = GRAY
        for v in outgoing[u]:
            if color[v] == WHITE:
                parent[v] = u
                dfs(v)
            elif color[v] == GRAY:
                cycles.append(reconstruct_cycle(u, v))
        color[u] = BLACK

    for node in outgoing:
        if color[node] == WHITE:
            dfs(node)

    unique: list[list[str]] = []
    seen = set()
    for cycle in cycles:
        sig = tuple(cycle)
        if sig not in seen:
            seen.add(sig)
            unique.append(cycle)

    return unique


def analyze_graph(files: list[FileNode], edges: list[GraphEdge]) -> GraphInsightsSchema:
    outgoing, incoming = build_adjacency(files, edges)

    return GraphInsightsSchema(
        isolated_files=detect_isolated_files(files, outgoing, incoming),
        top_incoming=top_degree_files(incoming, limit=10),
        top_outgoing=top_degree_files(outgoing, limit=10),
        connected_components=connected_components(files, outgoing, incoming),
        cycles=detect_cycles(outgoing),
    )