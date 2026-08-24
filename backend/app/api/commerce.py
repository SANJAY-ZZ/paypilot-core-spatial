from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.merchant import Merchant
from backend.app.schemas.commerce import CommerceReadinessResponse
from backend.app.services.commerce_service import commerce_service
from backend.app.core.errors import PayPilotBaseException

router = APIRouter(prefix="", tags=["Commerce Readiness"])


@router.get("/commerce-readiness", response_model=CommerceReadinessResponse)
def get_commerce_readiness(
    merchant_id: Optional[str] = Query(None, description="Merchant ID"),
    db: Session = Depends(get_db),
):
    """
    Evaluate and return the merchant's AI Commerce Readiness Score,
    including catalog structure, inventory visibility, and policy configuration.
    """
    if not merchant_id:
        merchant = db.query(Merchant).first()
        if not merchant:
            raise PayPilotBaseException("No merchant record found.", status_code=404)
        merchant_id = merchant.id

    return commerce_service.evaluate_readiness(db, merchant_id)
