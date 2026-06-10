from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.models.file_model import FileNode
from app.models.graph_model import GraphEdge, GraphNode
from app.models.metrics_model import FileMetrics


class AnalyzeRequest(BaseModel):
    repo_path: str = Field(..., description="Absolute or relative path to the repository")
    include_ai_summary: bool = Field(default=False, description="Generate AI summaries if enabled")


class AnalysisStats(BaseModel):
    total_files: int
    total_loc: int
    total_blank_lines: int
    total_comment_lines: int
    total_code_lines: int
    total_complexity: int
    average_complexity: float
    top_complex_files: list[dict[str, Any]]


class GraphInsightsSchema(BaseModel):
    isolated_files: list[str] = Field(default_factory=list)
    top_incoming: list[dict[str, Any]] = Field(default_factory=list)
    top_outgoing: list[dict[str, Any]] = Field(default_factory=list)
    connected_components: list[list[str]] = Field(default_factory=list)
    cycles: list[list[str]] = Field(default_factory=list)


class AnalysisResponse(BaseModel):
    repo_path: str
    files: list[FileNode]
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    file_metrics: dict[str, FileMetrics]
    stats: AnalysisStats
    graph_insights: GraphInsightsSchema
    repo_hash: str
    dependency_map: dict[str, list[str]]


class FileSummaryRequest(BaseModel):
    repo_path: str = Field(..., description="Path to the repository root")
    file_path: str = Field(..., description="Repository-relative file path or absolute file path")


class FileSummaryResponse(BaseModel):
    repo_path: str
    file_path: str
    language: str
    size: int
    file_hash: str | None = None
    cached: bool = False
    summary: str


class RepositorySummaryRequest(BaseModel):
    repo_path: str = Field(..., description="Path to the repository root")


class RepositorySummaryResponse(BaseModel):
    repo_path: str
    total_files: int
    language_breakdown: dict[str, int]
    cached: bool = False
    summary: str


class ArchitectureSummaryRequest(BaseModel):
    repo_path: str = Field(..., description="Path to the repository root")


class ArchitectureSummaryResponse(BaseModel):
    repo_path: str
    repo_hash: str
    cached: bool = False

    total_files: int
    language_breakdown: dict[str, int]

    stats: AnalysisStats
    graph_insights: GraphInsightsSchema

    overview: str
    main_modules: list[str] = Field(default_factory=list)
    hotspots: list[str] = Field(default_factory=list)
    refactoring_suggestions: list[str] = Field(default_factory=list)