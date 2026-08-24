from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.merchant import Merchant
from backend.app.models.guardian_policy import GuardianPolicy
from backend.app.schemas.guardian import (
    GuardianPolicyResponse,
    GuardianPolicyUpdate,
)
from backend.app.services.guardian_service import guardian_service
from backend.app.services.audit_service import audit_service
from backend.app.core.errors import PayPilotBaseException

router = APIRouter(prefix="/guardian", tags=["Guardian"])


@router.get("/policies", response_model=GuardianPolicyResponse)
def get_guardian_policy(
    merchant_id: Optional[str] = Query(None, description="Merchant ID"),
    db: Session = Depends(get_db),
):
    """Retrieve active deterministic Guardian policy rules for the merchant."""
    if not merchant_id:
        merchant = db.query(Merchant).first()
        if not merchant:
            raise PayPilotBaseException("No merchant record found.", status_code=404)
        merchant_id = merchant.id

    policy = guardian_service.get_or_create_policy(db, merchant_id)
    return GuardianPolicyResponse.model_validate(policy)


@router.put("/policies", response_model=GuardianPolicyResponse)
def update_guardian_policy(
    update_data: GuardianPolicyUpdate,
    merchant_id: Optional[str] = Query(None, description="Merchant ID"),
    db: Session = Depends(get_db),
):
    """Update merchant-defined Guardian financial limits and safety thresholds."""
    if not merchant_id:
        merchant = db.query(Merchant).first()
        if not merchant:
            raise PayPilotBaseException("No merchant record found.", status_code=404)
        merchant_id = merchant.id

    policy = guardian_service.get_or_create_policy(db, merchant_id)

    if update_data.max_discount_percent is not None:
        policy.max_discount_percent = update_data.max_discount_percent
    if update_data.max_campaign_budget is not None:
        policy.max_campaign_budget = update_data.max_campaign_budget
    if update_data.max_customer_count is not None:
        policy.max_customer_count = update_data.max_customer_count
    if update_data.min_ai_confidence is not None:
        policy.min_ai_confidence = update_data.min_ai_confidence
    if update_data.require_approval_above_amount is not None:
        policy.require_approval_above_amount = update_data.require_approval_above_amount

    db.commit()
    db.refresh(policy)

    # Record policy update in audit trail
    audit_service.record_event(
        db=db,
        merchant_id=merchant_id,
        agent="guardian",
        event_type="GUARDIAN_POLICY_UPDATED",
        reason="Merchant updated Guardian financial guardrail parameters.",
        metadata=update_data.model_dump(exclude_none=True),
    )

    return GuardianPolicyResponse.model_validate(policy)
