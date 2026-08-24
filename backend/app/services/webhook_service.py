import hmac
import hashlib
import json
import logging
from typing import Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.errors import PayPilotBaseException
from backend.app.models.processed_webhook_event import ProcessedWebhookEvent
from backend.app.models.payment import Payment
from backend.app.models.ai_action import AIAction
from backend.app.models.merchant import Merchant
from backend.app.services.audit_service import audit_service

logger = logging.getLogger(__name__)


class WebhookService:
    """Handles incoming Razorpay Webhooks with HMAC SHA256 signature verification and idempotency."""

    @staticmethod
    def verify_signature(raw_body: bytes, signature: str, secret: Optional[str] = None) -> bool:
        webhook_secret = secret or settings.RAZORPAY_WEBHOOK_SECRET
        if not webhook_secret:
            logger.error("RAZORPAY_WEBHOOK_SECRET is not configured.")
            return False

        if not signature:
            return False

        expected_signature = hmac.new(
            webhook_secret.encode("utf-8"),
            raw_body,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected_signature, signature)

    @classmethod
    def process_webhook_event(
        cls,
        db: Session,
        raw_body: bytes,
        signature: str,
    ) -> Tuple[Dict[str, Any], int]:
        # 1. Verify Signature
        if not cls.verify_signature(raw_body, signature):
            raise PayPilotBaseException("Invalid Razorpay webhook signature.", status_code=400)

        try:
            event_data = json.loads(raw_body.decode("utf-8"))
        except Exception as e:
            raise PayPilotBaseException(f"Invalid JSON webhook payload: {str(e)}", status_code=400)

        event_id = event_data.get("event_id") or event_data.get("id")
        event_type = event_data.get("event", "unknown")

        if not event_id:
            raise PayPilotBaseException("Missing event_id in webhook payload.", status_code=400)

        # 2. Check Event Idempotency
        existing_event = (
            db.query(ProcessedWebhookEvent)
            .filter(ProcessedWebhookEvent.event_id == event_id)
            .first()
        )
        if existing_event:
            logger.info(f"Duplicate webhook event ignored: {event_id} ({event_type})")
            return {
                "status": "success",
                "message": "Duplicate event acknowledged without reprocessing.",
                "event_id": event_id,
                "event_type": event_type,
                "idempotent": True,
            }, 200

        # Record event in processed events table
        processed_rec = ProcessedWebhookEvent(
            event_id=event_id,
            event_type=event_type,
        )
        db.add(processed_rec)
        db.commit()

        # 3. Handle Supported Event Types
        payload = event_data.get("payload", {})

        # Default merchant fallback
        merchant = db.query(Merchant).first()
        merchant_id = merchant.id if merchant else "mer_koraretail"

        if event_type == "payment_link.paid":
            plink_entity = payload.get("payment_link", {}).get("entity", {})
            payment_entity = payload.get("payment", {}).get("entity", {})

            link_id = plink_entity.get("id")
            ref_id = plink_entity.get("reference_id")
            amount_paise = plink_entity.get("amount", payment_entity.get("amount", 0))
            amount_inr = round(amount_paise / 100.0, 2)
            payment_id = payment_entity.get("id")

            # A. Match and update AIAction if reference or link ID matches
            matched_action = None
            if ref_id:
                matched_action = db.query(AIAction).filter(AIAction.idempotency_key == ref_id).first()
            if not matched_action and link_id:
                matched_action = (
                    db.query(AIAction)
                    .filter(AIAction.execution_result.isnot(None))
                    .all()
                )
                matched_action = next(
                    (a for a in matched_action if a.execution_result and a.execution_result.get("payment_link_id") == link_id),
                    None,
                )

            if matched_action:
                matched_action.status = "executed"
                if not matched_action.execution_result:
                    matched_action.execution_result = {}
                matched_action.execution_result["webhook_payment_id"] = payment_id
                matched_action.execution_result["paid_at_webhook"] = True
                merchant_id = matched_action.merchant_id

            # B. Match and update Payment record
            matched_payment = None
            if payment_id:
                matched_payment = db.query(Payment).filter(Payment.razorpay_reference == payment_id).first()
            if not matched_payment and ref_id:
                matched_payment = db.query(Payment).filter(Payment.razorpay_reference == ref_id).first()

            if matched_payment:
                matched_payment.status = "success"
                merchant_id = matched_payment.merchant_id

            db.commit()

            # C. Record EXECUTION_SUCCESS Audit Event
            audit_service.record_event(
                db=db,
                merchant_id=merchant_id,
                action_id=matched_action.id if matched_action else None,
                agent="executor",
                event_type="EXECUTION_SUCCESS",
                reason=f"Payment link {link_id} paid successfully (Amount: ₹{amount_inr:,.0f}).",
                metadata={
                    "event_id": event_id,
                    "payment_link_id": link_id,
                    "razorpay_payment_id": payment_id,
                    "reference_id": ref_id,
                    "amount": amount_inr,
                    "currency": "INR",
                },
                status="success",
            )

            return {
                "status": "success",
                "message": f"Payment link {link_id} processed successfully.",
                "event_id": event_id,
                "event_type": event_type,
            }, 200

        elif event_type == "payment.failed":
            payment_entity = payload.get("payment", {}).get("entity", {})
            payment_id = payment_entity.get("id")
            error_desc = payment_entity.get("error_description", "Payment failed via gateway")

            # Update matching payment
            if payment_id:
                matched_payment = db.query(Payment).filter(Payment.razorpay_reference == payment_id).first()
                if matched_payment:
                    matched_payment.status = "failed"
                    matched_payment.failure_reason = error_desc
                    db.commit()

            audit_service.record_event(
                db=db,
                merchant_id=merchant_id,
                agent="executor",
                event_type="PAYMENT_FAILED",
                reason=f"Razorpay payment failure: {error_desc}",
                metadata={"payment_id": payment_id, "event_id": event_id},
                status="failed",
            )

            return {
                "status": "success",
                "message": "Payment failure event recorded.",
                "event_id": event_id,
            }, 200

        elif event_type == "payment_link.cancelled":
            plink_entity = payload.get("payment_link", {}).get("entity", {})
            link_id = plink_entity.get("id")

            audit_service.record_event(
                db=db,
                merchant_id=merchant_id,
                agent="executor",
                event_type="PAYMENT_LINK_CANCELLED",
                reason=f"Payment link {link_id} was cancelled.",
                metadata={"payment_link_id": link_id, "event_id": event_id},
                status="cancelled",
            )

            return {
                "status": "success",
                "message": "Payment link cancellation acknowledged.",
                "event_id": event_id,
            }, 200

        else:
            logger.info(f"Received unhandled webhook event: {event_type}")
            return {
                "status": "success",
                "message": f"Webhook event '{event_type}' acknowledged.",
                "event_id": event_id,
                "unhandled": True,
            }, 200


webhook_service = WebhookService()
