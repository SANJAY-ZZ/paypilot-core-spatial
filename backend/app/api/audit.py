from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.merchant import Merchant
from backend.app.schemas.audit import (
    AuditEventResponse,
    AuditListResponse,
)
from backend.app.agents.auditor import AuditorAgent

router = APIRouter(prefix="/audit", tags=["Audit"])


@router.get("", response_model=AuditListResponse)
def get_audit_trail(
    merchant_id: Optional[str] = Query(None, description="Filter by Merchant ID"),
    action_id: Optional[str] = Query(None, description="Filter by Action ID"),
    agent: Optional[str] = Query(None, description="Filter by Agent name (scout, analyst, strategist, guardian, executor, auditor)"),
    event_type: Optional[str] = Query(None, description="Filter by Event Type (e.g. GUARDIAN_APPROVED, EXECUTION_SUCCESS)"),
    status: Optional[str] = Query(None, description="Filter by event status"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Retrieve immutable chronological audit trail of agent decisions and execution steps."""
    if not merchant_id:
        merchant = db.query(Merchant).first()
        if merchant:
            merchant_id = merchant.id

    offset = (page - 1) * limit
    events, total = AuditorAgent.query_logs(
        db=db,
        merchant_id=merchant_id,
        action_id=action_id,
        agent=agent,
        event_type=event_type,
        status=status,
        limit=limit,
        offset=offset,
    )

    return AuditListResponse(
        items=[AuditEventResponse.model_validate(e) for e in events],
        total=total,
        page=page,
        limit=limit,
    )
