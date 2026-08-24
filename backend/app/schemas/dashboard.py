from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from backend.app.schemas.opportunity import OpportunityResponse
from backend.app.schemas.action import ActionResponse


class DashboardMetric(BaseModel):
    label: str
    value: Any
    unit: Optional[str] = None
    change_percentage: Optional[float] = None
    trend: Optional[str] = None  # "up", "down", "neutral"


class OpportunityTypeBreakdown(BaseModel):
    type: str
    label: str
    count: int
    potential_revenue: float


class DashboardResponse(BaseModel):
    merchant_id: str
    merchant_name: str
    currency: str
    total_revenue: float
    customer_count: int
    transaction_count: int
    recoverable_revenue: float
    opportunity_count: int
    recovery_rate: float
    ai_actions_today: int
    metrics_cards: List[DashboardMetric]
    opportunity_breakdown: List[OpportunityTypeBreakdown]
    recent_opportunities: List[OpportunityResponse]
    recent_actions: List[ActionResponse]
