from typing import Optional
from fastapi import APIRouter, Depends, Query, Header, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.merchant import Merchant
from backend.app.schemas.action import (
    ActionPreviewRequest,
    ActionPreviewResponse,
    ActionApproveRequest,
    ActionExecuteRequest,
    ActionResponse,
    ActionListResponse,
)
from backend.app.services.action_service import action_service

router = APIRouter(prefix="/actions", tags=["Actions"])


@router.post("/preview", response_model=ActionPreviewResponse, status_code=status.HTTP_200_OK)
def preview_action(
    request: ActionPreviewRequest,
    db: Session = Depends(get_db),
):
    """
    Generate an AI proposed action for an opportunity and evaluate it against Guardian policies.
    """
    return action_service.preview_action(db, request)


@router.post("/approve", response_model=ActionResponse, status_code=status.HTTP_200_OK)
def approve_action(
    request: ActionApproveRequest,
    db: Session = Depends(get_db),
):
    """
    Explicitly approve an action that is in 'awaiting_approval' status.
    """
    return action_service.approve_action(db, request)


@router.post("/execute", response_model=ActionResponse, status_code=status.HTTP_200_OK)
def execute_action(
    request: ActionExecuteRequest,
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key"),
    db: Session = Depends(get_db),
):
    """
    Execute an approved action via the Mock Razorpay adapter.
    Enforces Guardian checks and idempotency deduplication.
    """
    # Accept idempotency key from header or request body
    effective_idempotency_key = x_idempotency_key or request.idempotency_key
    request.idempotency_key = effective_idempotency_key

    return action_service.execute_action(db, request)


@router.get("", response_model=ActionListResponse)
def list_actions(
    merchant_id: Optional[str] = Query(None, description="Merchant ID"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """List recent AI actions and execution results."""
    if not merchant_id:
        merchant = db.query(Merchant).first()
        merchant_id = merchant.id if merchant else "mer_koraretail"

    actions, total = action_service.list_actions(db, merchant_id, limit=limit, offset=offset)
    return ActionListResponse(
        items=[ActionResponse.model_validate(a) for a in actions],
        total=total,
    )


@router.get("/{action_id}", response_model=ActionResponse)
def get_action(
    action_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve details and execution results of a specific action."""
    return action_service.get_action(db, action_id)
