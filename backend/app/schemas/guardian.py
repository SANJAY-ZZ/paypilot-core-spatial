from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class PolicyCheckDetail(BaseModel):
    rule_name: str
    passed: bool
    threshold: Any
    actual_value: Any
    message: str


class GuardianEvaluationResult(BaseModel):
    decision: str = Field(..., description="Decision: 'approved', 'blocked', or 'requires_approval'")
    reason: str
    risk_level: str = "low"
    policy_checks: List[PolicyCheckDetail] = []
    metadata: Optional[Dict[str, Any]] = None


class GuardianPolicyBase(BaseModel):
    max_discount_percent: float = Field(default=15.0, ge=0.0, le=100.0)
    max_campaign_budget: float = Field(default=10000.0, ge=0.0)
    max_customer_count: int = Field(default=500, ge=1)
    min_ai_confidence: float = Field(default=0.75, ge=0.0, le=1.0)
    require_approval_above_amount: float = Field(default=5000.0, ge=0.0)


class GuardianPolicyResponse(GuardianPolicyBase):
    id: str
    merchant_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GuardianPolicyUpdate(BaseModel):
    max_discount_percent: Optional[float] = Field(None, ge=0.0, le=100.0)
    max_campaign_budget: Optional[float] = Field(None, ge=0.0)
    max_customer_count: Optional[int] = Field(None, ge=1)
    min_ai_confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    require_approval_above_amount: Optional[float] = Field(None, ge=0.0)
