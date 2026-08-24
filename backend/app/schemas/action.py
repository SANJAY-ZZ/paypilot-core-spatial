from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict, Field
from backend.app.schemas.guardian import GuardianEvaluationResult


class ActionPreviewRequest(BaseModel):
    opportunity_id: str
    merchant_id: Optional[str] = None
    override_discount_percent: Optional[float] = None
    override_budget: Optional[float] = None
    target_customer_ids: Optional[List[str]] = None


class ActionPreviewResponse(BaseModel):
    action_id: str
    opportunity_id: str
    merchant_id: str
    agent: str
    action_type: str
    confidence: float
    status: str
    payload: Dict[str, Any]
    guardian_result: GuardianEvaluationResult
    estimated_revenue: float
    estimated_cost: float
    created_at: datetime


class ActionApproveRequest(BaseModel):
    action_id: str
    merchant_id: Optional[str] = None
    approval_notes: Optional[str] = None


class ActionExecuteRequest(BaseModel):
    action_id: str
    merchant_id: Optional[str] = None
    idempotency_key: Optional[str] = None


class ActionResponse(BaseModel):
    id: str
    merchant_id: str
    opportunity_id: Optional[str] = None
    agent: str
    action_type: str
    payload: Dict[str, Any]
    confidence: float
    status: str
    guardian_result: Optional[Dict[str, Any]] = None
    execution_result: Optional[Dict[str, Any]] = None
    idempotency_key: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActionListResponse(BaseModel):
    items: List[ActionResponse]
    total: int
