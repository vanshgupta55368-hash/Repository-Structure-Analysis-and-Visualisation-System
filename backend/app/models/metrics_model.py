from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ComplexityBreakdown(BaseModel):
    """
    Gives a transparent breakdown of the complexity score.
    This is useful because you can explain why a file is complex.
    """

    model_config = ConfigDict(extra="ignore")

    branches: int = 0
    loops: int = 0
    function_defs: int = 0
    class_defs: int = 0
    exception_blocks: int = 0
    boolean_ops: int = 0
    total: int = 0


class FileMetrics(BaseModel):
    """
    Per-file code metrics.
    """

    model_config = ConfigDict(extra="ignore")

    loc: int = Field(default=0, ge=0, description="Total lines of code")
    blank_lines: int = Field(default=0, ge=0)
    comment_lines: int = Field(default=0, ge=0)
    code_lines: int = Field(default=0, ge=0)

    complexity: int = Field(default=0, ge=0, description="Cyclomatic-style complexity estimate")
    complexity_breakdown: ComplexityBreakdown = Field(default_factory=ComplexityBreakdown)

    num_imports: int = Field(default=0, ge=0)
    num_dependencies: int = Field(default=0, ge=0)

    max_line_length: int = Field(default=0, ge=0)
    avg_line_length: float = Field(default=0.0, ge=0.0)

    long_lines: int = Field(default=0, ge=0, description="Lines above a chosen threshold")
    functions: int = Field(default=0, ge=0)
    classes: int = Field(default=0, ge=0)

    score: Optional[float] = Field(default=None, description="Optional overall quality score")
    notes: list[str] = Field(default_factory=list)


class RepositoryMetrics(BaseModel):
    """
    Aggregated metrics for the whole repository.
    """

    model_config = ConfigDict(extra="ignore")

    total_files: int = Field(default=0, ge=0)
    total_loc: int = Field(default=0, ge=0)
    total_blank_lines: int = Field(default=0, ge=0)
    total_comment_lines: int = Field(default=0, ge=0)
    total_code_lines: int = Field(default=0, ge=0)
    total_complexity: int = Field(default=0, ge=0)
    average_complexity: float = Field(default=0.0, ge=0.0)

    most_complex_files: list[dict] = Field(default_factory=list)
    largest_files: list[dict] = Field(default_factory=list)
    language_breakdown: dict[str, int] = Field(default_factory=dict)