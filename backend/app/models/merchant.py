import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class Merchant(Base):
    __tablename__ = "merchants"

    id = Column(String(64), primary_key=True, default=lambda: f"mer_{uuid.uuid4().hex[:12]}")
    name = Column(String(255), nullable=False)
    currency = Column(String(10), default="INR", nullable=False)
    total_revenue = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    customers = relationship("Customer", back_populates="merchant", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="merchant", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="merchant", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="merchant", cascade="all, delete-orphan")
    opportunities = relationship("Opportunity", back_populates="merchant", cascade="all, delete-orphan")
    actions = relationship("AIAction", back_populates="merchant", cascade="all, delete-orphan")
    guardian_policy = relationship("GuardianPolicy", back_populates="merchant", uselist=False, cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="merchant", cascade="all, delete-orphan")
