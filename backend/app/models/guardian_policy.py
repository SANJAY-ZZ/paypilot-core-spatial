import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class GuardianPolicy(Base):
    __tablename__ = "guardian_policies"

    id = Column(String(64), primary_key=True, default=lambda: f"pol_{uuid.uuid4().hex[:12]}")
    merchant_id = Column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    max_discount_percent = Column(Float, default=15.0, nullable=False)
    max_campaign_budget = Column(Float, default=10000.0, nullable=False)
    max_customer_count = Column(Integer, default=500, nullable=False)
    min_ai_confidence = Column(Float, default=0.75, nullable=False)
    require_approval_above_amount = Column(Float, default=5000.0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    merchant = relationship("Merchant", back_populates="guardian_policy")
