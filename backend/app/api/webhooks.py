from fastapi import APIRouter, Depends, Header, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.services.webhook_service import webhook_service
from backend.app.core.errors import PayPilotBaseException

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


@router.post("/razorpay", status_code=status.HTTP_200_OK)
async def handle_razorpay_webhook(
    request: Request,
    x_razorpay_signature: str = Header(..., alias="X-Razorpay-Signature"),
    db: Session = Depends(get_db),
):
    """
    Process incoming Razorpay webhook events with signature verification and idempotency.
    """
    raw_body = await request.body()
    result, status_code = webhook_service.process_webhook_event(
        db=db,
        raw_body=raw_body,
        signature=x_razorpay_signature,
    )
    return JSONResponse(status_code=status_code, content=result)
