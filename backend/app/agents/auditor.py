from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from backend.app.models.audit_event import AuditEvent
from backend.app.services.audit_service import audit_service


class AuditorAgent:
    """
    AUDITOR AGENT:
    Maintains an immutable, chronologically ordered audit log of all system decisions,
    policy checks, approvals, and transaction dispatches.
    """

    NAME = "auditor"

    @classmethod
    def record(
        cls,
        db: Session,
        merchant_id: str,
        agent: str,
        event_type: str,
        reason: str,
        action_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        status: str = "recorded",
    ) -> AuditEvent:
        return audit_service.record_event(
            db=db,
            merchant_id=merchant_id,
            action_id=action_id,
            agent=agent,
            event_type=event_type,
            reason=reason,
            metadata=metadata,
            status=status,
        )

    @classmethod
    def query_logs(
        cls,
        db: Session,
        merchant_id: Optional[str] = None,
        action_id: Optional[str] = None,
        agent: Optional[str] = None,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[AuditEvent], int]:
        return audit_service.get_events(
            db=db,
            merchant_id=merchant_id,
            action_id=action_id,
            agent=agent,
            event_type=event_type,
            status=status,
            limit=limit,
            offset=offset,
        )
