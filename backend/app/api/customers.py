from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.core.database import get_db
from backend.app.models.customer import Customer
from backend.app.models.merchant import Merchant
from backend.app.models.payment import Payment
from backend.app.schemas.customer import (
    CustomerResponse,
    CustomerDetailResponse,
    CustomerListResponse,
)
from backend.app.core.errors import CustomerNotFoundError

router = APIRouter(prefix="/customers", tags=["Customers"])


@router.get("", response_model=CustomerListResponse)
def list_customers(
    merchant_id: Optional[str] = Query(None, description="Merchant ID"),
    min_ltv: Optional[float] = Query(None, description="Minimum Lifetime Value"),
    min_churn_risk: Optional[float] = Query(None, description="Minimum Churn Risk (0.0-1.0)"),
    search: Optional[str] = Query(None, description="Search by name or email"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=200, description="Items per page"),
    db: Session = Depends(get_db),
):
    """Retrieve paginated merchant customers with cohort metrics."""
    query = db.query(Customer)

    if merchant_id:
        query = query.filter(Customer.merchant_id == merchant_id)
    else:
        merchant = db.query(Merchant).first()
        if merchant:
            query = query.filter(Customer.merchant_id == merchant.id)

    if min_ltv is not None:
        query = query.filter(Customer.lifetime_value >= min_ltv)
    if min_churn_risk is not None:
        query = query.filter(Customer.churn_risk >= min_churn_risk)
    if search:
        query = query.filter((Customer.name.ilike(f"%{search}%")) | (Customer.email.ilike(f"%{search}%")))

    total = query.count()
    offset = (page - 1) * limit
    customers = query.order_by(desc(Customer.lifetime_value)).offset(offset).limit(limit).all()

    return CustomerListResponse(
        items=[CustomerResponse.model_validate(c) for c in customers],
        total=total,
        page=page,
        limit=limit,
    )


@router.get("/{customer_id}", response_model=CustomerDetailResponse)
def get_customer(
    customer_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve detailed customer profile and behavioral segments."""
    cust = db.query(Customer).filter(Customer.id == customer_id).first()
    if not cust:
        raise CustomerNotFoundError(customer_id)

    # Segment classification
    if cust.lifetime_value > 8000:
        segment = "VIP High-Spender"
    elif cust.churn_risk > 0.65:
        segment = "Dormant / At-Risk"
    elif cust.repeat_probability > 0.75:
        segment = "Loyal Repeat Buyer"
    else:
        segment = "Active Regular"

    # Count recent failed payments
    failed_pmts = (
        db.query(Payment)
        .filter(Payment.customer_id == cust.id, Payment.status == "failed")
        .count()
    )

    return CustomerDetailResponse(
        id=cust.id,
        merchant_id=cust.merchant_id,
        name=cust.name,
        email=cust.email,
        lifetime_value=cust.lifetime_value,
        order_count=cust.order_count,
        average_order_value=cust.average_order_value,
        last_purchase_at=cust.last_purchase_at,
        churn_risk=cust.churn_risk,
        repeat_probability=cust.repeat_probability,
        upsell_probability=cust.upsell_probability,
        created_at=cust.created_at,
        segment=segment,
        total_spent=cust.lifetime_value,
        recent_failed_payments=failed_pmts,
    )
