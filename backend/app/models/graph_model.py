from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class GraphNode(BaseModel):
    """
    Node format used by React Flow and the backend graph layer.
    """

    model_config = ConfigDict(extra="ignore")

    id: str = Field(..., description="Unique graph node id")
    label: str = Field(..., description="Display label")
    type: str = Field(default="file", description="Node type, e.g. file/module/package")
    group: Optional[str] = Field(default=None, description="Optional grouping key")
    file_path: Optional[str] = Field(default=None, description="Underlying file path")
    language: Optional[str] = Field(default=None, description="Detected language")
    x: float = Field(default=0.0)
    y: float = Field(default=0.0)
    data: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    """
    Directed edge between two graph nodes.
    """

    model_config = ConfigDict(extra="ignore")

    source: str = Field(..., description="Source node id")
    target: str = Field(..., description="Target node id")
    relation: str = Field(default="import", description="Type of relationship")
    weight: float = Field(default=1.0, ge=0.0)
    bidirectional: bool = Field(default=False)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphStats(BaseModel):
    """
    Useful graph-level statistics.
    """

    model_config = ConfigDict(extra="ignore")

    node_count: int = 0
    edge_count: int = 0
    isolated_nodes: int = 0
    cyclic_nodes: int = 0
    max_out_degree: int = 0
    max_in_degree: int = 0


class GraphResponse(BaseModel):
    """
    Final graph payload returned by the backend.
    """

    model_config = ConfigDict(extra="ignore")

    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    stats: GraphStats = Field(default_factory=GraphStats)
    repo_hash: Optional[str] = None