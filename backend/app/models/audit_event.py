import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(String(64), primary_key=True, default=lambda: f"aud_{uuid.uuid4().hex[:12]}")
    merchant_id = Column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    action_id = Column(String(64), ForeignKey("ai_actions.id", ondelete="SET NULL"), nullable=True, index=True)
    agent = Column(String(64), nullable=False)
    event_type = Column(String(64), nullable=False, index=True)
    reason = Column(Text, nullable=False)
    metadata_json = Column(JSON, default=dict, nullable=False)
    status = Column(String(50), default="recorded", nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    merchant = relationship("Merchant", back_populates="audit_events")
    action = relationship("AIAction", back_populates="audit_events")

    __table_args__ = (
        Index("ix_audit_events_merchant_created", "merchant_id", "created_at"),
        Index("ix_audit_events_agent", "agent"),
    )
