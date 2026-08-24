from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class OpportunityBase(BaseModel):
    type: str = Field(..., description="Type of opportunity: payment_recovery, customer_winback, upsell, subscription_recovery")
    title: str
    potential_revenue: float
    confidence: float
    risk: str
    affected_customer_count: int
    reason: str
    recommended_action: str
    status: str = "discovered"


class OpportunityCreate(OpportunityBase):
    merchant_id: str


class OpportunityResponse(OpportunityBase):
    id: str
    merchant_id: str
    created_at: datetime
    reasoning_source: Optional[str] = "deterministic"
    reasoning: Optional[str] = None
    key_factors: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)

    def model_post_init(self, __context: Any) -> None:
        if not self.reasoning and self.reason:
            self.reasoning = self.reason
        if not self.key_factors:
            self.key_factors = [
                f"{self.affected_customer_count} customers in target cohort",
                f"₹{self.potential_revenue:,.0f} estimated revenue opportunity",
                f"{int(self.confidence * 100)}% model confidence assessment",
            ]


class OpportunityDetailResponse(OpportunityResponse):
    metadata: Optional[Dict[str, Any]] = None
    historical_recovery_rate: Optional[float] = None
    suggested_payload: Optional[Dict[str, Any]] = None


class OpportunityListResponse(BaseModel):
    items: List[OpportunityResponse]
    total: int
    total_potential_revenue: float
