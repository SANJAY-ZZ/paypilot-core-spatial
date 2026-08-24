import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(String(64), primary_key=True, default=lambda: f"prod_{uuid.uuid4().hex[:12]}")
    merchant_id = Column(String(64), ForeignKey("merchants.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False, index=True)
    price = Column(Float, nullable=False)
    inventory = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    merchant = relationship("Merchant", back_populates="products")
