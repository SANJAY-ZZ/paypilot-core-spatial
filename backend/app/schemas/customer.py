from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class CustomerBase(BaseModel):
    name: str
    email: str
    lifetime_value: float
    order_count: int
    average_order_value: float
    last_purchase_at: Optional[datetime] = None
    churn_risk: float
    repeat_probability: float
    upsell_probability: float


class CustomerResponse(CustomerBase):
    id: str
    merchant_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CustomerDetailResponse(CustomerResponse):
    segment: Optional[str] = None
    total_spent: Optional[float] = None
    recent_failed_payments: Optional[int] = 0


class CustomerListResponse(BaseModel):
    items: List[CustomerResponse]
    total: int
    page: int
    limit: int
