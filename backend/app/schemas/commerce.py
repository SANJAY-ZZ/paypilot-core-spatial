from typing import List, Dict, Any
from pydantic import BaseModel


class ReadinessCategoryScore(BaseModel):
    category: str
    score: int  # 0 to 100
    weight: float
    status: str  # optimal, good, needs_improvement, critical
    details: str
    metrics: Dict[str, Any]


class ReadinessRecommendation(BaseModel):
    id: str
    title: str
    impact: str  # high, medium, low
    category: str
    description: str
    action_type: str


class CommerceReadinessResponse(BaseModel):
    merchant_id: str
    merchant_name: str
    overall_score: int  # 0 to 100
    grade: str  # A+, A, B, C, D
    summary: str
    categories: List[ReadinessCategoryScore]
    recommendations: List[ReadinessRecommendation]
