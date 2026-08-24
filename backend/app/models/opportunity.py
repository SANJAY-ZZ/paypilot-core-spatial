import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class Opportunity(Base):
    __tablename__ = "opportunities"

    id = Column(String(64), primary_key=True, default=lambda: f"opp_{uuid.uuid4().hex[:12]}")
    merchant_id = Column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(64), nullable=False)  # payment_recovery, customer_winback, upsell, subscription_recovery
    title = Column(String(255), nullable=False)
    potential_revenue = Column(Float, default=0.0, nullable=False)
    confidence = Column(Float, default=0.0, nullable=False)
    risk = Column(String(32), default="low", nullable=False)  # low, medium, high
    affected_customer_count = Column(Integer, default=0, nullable=False)
    reason = Column(Text, nullable=False)
    recommended_action = Column(String(255), nullable=False)
    status = Column(String(50), default="discovered", nullable=False)  # discovered, analyzed, action_proposed, in_progress, completed, dismissed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    merchant = relationship("Merchant", back_populates="opportunities")
    actions = relationship("AIAction", back_populates="opportunity", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_opportunities_merchant_type", "merchant_id", "type"),
        Index("ix_opportunities_merchant_status", "merchant_id", "status"),
    )
