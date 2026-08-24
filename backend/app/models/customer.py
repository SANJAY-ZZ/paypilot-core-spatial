import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(String(64), primary_key=True, default=lambda: f"cust_{uuid.uuid4().hex[:12]}")
    merchant_id = Column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False)
    lifetime_value = Column(Float, default=0.0, nullable=False)
    order_count = Column(Integer, default=0, nullable=False)
    average_order_value = Column(Float, default=0.0, nullable=False)
    last_purchase_at = Column(DateTime, nullable=True)
    churn_risk = Column(Float, default=0.0, nullable=False)
    repeat_probability = Column(Float, default=0.0, nullable=False)
    upsell_probability = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    merchant = relationship("Merchant", back_populates="customers")
    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="customer", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_customers_merchant_churn", "merchant_id", "churn_risk"),
        Index("ix_customers_merchant_ltv", "merchant_id", "lifetime_value"),
    )
