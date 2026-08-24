from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class SimulationRequest(BaseModel):
    discount_percent: float = Field(..., ge=0, le=100, description="Proposed discount percentage (0-100)")
    campaign_budget: float = Field(..., ge=0, description="Campaign marketing budget in merchant currency")
    customer_count: int = Field(..., ge=1, description="Number of targeted customers")
    average_order_value: float = Field(..., ge=0, description="Baseline average order value (AOV)")
    conversion_rate: float = Field(..., ge=0, le=1.0, description="Expected conversion rate (0.0 - 1.0)")
    duration_days: int = Field(default=14, ge=1, le=365, description="Campaign duration in days")


class SimulationBreakdown(BaseModel):
    gross_revenue: float
    total_discount_cost: float
    marketing_cost: float
    net_gain: float
    roi_percentage: float
    cost_per_acquisition: float
    revenue_per_targeted_customer: float


class SimulationResponse(BaseModel):
    expected_orders: int
    expected_revenue: float
    campaign_cost: float
    projected_net_gain: float
    confidence: float
    recommendation: str
    breakdown: SimulationBreakdown
    risk_level: str
    guardian_precheck_status: str  # "compliant" | "requires_guardian_override" | "violates_policy"
