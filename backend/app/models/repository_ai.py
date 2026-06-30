from pydantic import BaseModel
from typing import List


class Recommendation(BaseModel):
    title: str
    description: str


class Hotspot(BaseModel):
    file: str
    reason: str
    severity: str


class Health(BaseModel):
    score: int
    maintainability: str
    architecture: str
    complexity: str
    summary: str


class RepositoryAIResponse(BaseModel):
    health: Health
    recommendations: List[Recommendation]
    hotspots: List[Hotspot]