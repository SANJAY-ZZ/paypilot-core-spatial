import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(String(64), primary_key=True, default=lambda: f"ord_{uuid.uuid4().hex[:12]}")
    merchant_id = Column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    customer_id = Column(String(64), ForeignKey("customers.id", ondelete="CASCADE"), nullable=False, index=True)
    total_amount = Column(Float, nullable=False)
    status = Column(String(50), default="completed", nullable=False)  # pending, completed, failed, cancelled
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    merchant = relationship("Merchant", back_populates="orders")
    customer = relationship("Customer", back_populates="orders")
    payments = relationship("Payment", back_populates="order")

    __table_args__ = (
        Index("ix_orders_merchant_created", "merchant_id", "created_at"),
    )
