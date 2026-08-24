import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(64), primary_key=True, default=lambda: f"pay_{uuid.uuid4().hex[:12]}")
    merchant_id = Column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(64), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    order_id = Column(String(64), ForeignKey("orders.id", ondelete="SET NULL"), nullable=True, index=True)
    amount = Column(Float, nullable=False)
    status = Column(String(50), default="success", nullable=False)  # success, failed, pending, refunded
    failure_reason = Column(String(255), nullable=True)
    razorpay_reference = Column(String(128), nullable=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    merchant = relationship("Merchant", back_populates="payments")
    customer = relationship("Customer", back_populates="payments")
    order = relationship("Order", back_populates="payments")

    __table_args__ = (
        Index("ix_payments_merchant_status", "merchant_id", "status"),
        Index("ix_payments_merchant_created", "merchant_id", "created_at"),
    )
