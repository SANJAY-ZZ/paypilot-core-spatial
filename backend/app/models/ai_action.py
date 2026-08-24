import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Index, JSON
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class AIAction(Base):
    __tablename__ = "ai_actions"

    id = Column(String(64), primary_key=True, default=lambda: f"act_{uuid.uuid4().hex[:12]}")
    merchant_id = Column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    opportunity_id = Column(String(64), ForeignKey("opportunities.id", ondelete="SET NULL"), nullable=True, index=True)
    agent = Column(String(64), default="strategist", nullable=False)
    action_type = Column(String(64), nullable=False)
    payload = Column(JSON, default=dict, nullable=False)
    confidence = Column(Float, default=0.0, nullable=False)
    status = Column(
        String(50),
        default="proposed",
        nullable=False,
    )  # proposed, awaiting_approval, approved, blocked, executing, executed, failed
    guardian_result = Column(JSON, nullable=True)
    execution_result = Column(JSON, nullable=True)
    idempotency_key = Column(String(128), nullable=True, unique=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    merchant = relationship("Merchant", back_populates="actions")
    opportunity = relationship("Opportunity", back_populates="actions")
    audit_events = relationship("AuditEvent", back_populates="action")

    __table_args__ = (
        Index("ix_ai_actions_merchant_status", "merchant_id", "status"),
    )
