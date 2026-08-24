from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.app.models.audit_event import AuditEvent


class AuditService:
    """Immutable audit trail management for PayPilot AI operations."""

    @staticmethod
    def record_event(
        db: Session,
        merchant_id: str,
        agent: str,
        event_type: str,
        reason: str,
        action_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        status: str = "recorded",
    ) -> AuditEvent:
        event = AuditEvent(
            merchant_id=merchant_id,
            action_id=action_id,
            agent=agent,
            event_type=event_type,
            reason=reason,
            metadata_json=metadata or {},
            status=status,
            created_at=datetime.now(timezone.utc),
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @staticmethod
    def get_events(
        db: Session,
        merchant_id: Optional[str] = None,
        action_id: Optional[str] = None,
        agent: Optional[str] = None,
        event_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> tuple[List[AuditEvent], int]:
        query = db.query(AuditEvent)

        if merchant_id:
            query = query.filter(AuditEvent.merchant_id == merchant_id)
        if action_id:
            query = query.filter(AuditEvent.action_id == action_id)
        if agent:
            query = query.filter(AuditEvent.agent == agent)
        if event_type:
            query = query.filter(AuditEvent.event_type == event_type)
        if status:
            query = query.filter(AuditEvent.status == status)

        total = query.count()
        events = query.order_by(desc(AuditEvent.created_at)).offset(offset).limit(limit).all()
        return events, total


audit_service = AuditService()
