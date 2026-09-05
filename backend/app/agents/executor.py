from typing import Dict, Any, Optional
import time
import logging
from sqlalchemy.orm import Session
from backend.app.models.ai_action import AIAction
from backend.app.models.merchant import Merchant
from backend.app.services.razorpay_service import get_razorpay_service
from backend.app.services.audit_service import audit_service
from backend.app.core.errors import GuardianBlockedError, ApprovalRequiredError, DuplicateExecutionError

logger = logging.getLogger(__name__)


class ExecutorAgent:
    """
    EXECUTOR AGENT:
    Executes approved financial and recovery actions via the Razorpay service adapter (Test or Mock Mode).
    Enforces Guardian compliance and idempotency guarantees.
    """

    NAME = "executor"

    @classmethod
    def execute_action(
        cls,
        db: Session,
        action: AIAction,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        # 1. Idempotency & Replay Checks
        # If action has already been executed, return existing result without calling payment gateway again
        if action.status == "executed" and action.execution_result:
            logger.info(f"Action '{action.id}' was already executed. Returning existing execution result.")
            return {
                "idempotent_replay": True,
                "action_id": action.id,
                "status": action.status,
                "execution_result": action.execution_result,
                "message": "Action was already successfully executed (idempotent replay).",
            }

        if idempotency_key:
            if action.idempotency_key == idempotency_key and action.status == "executed":
                return {
                    "idempotent_replay": True,
                    "action_id": action.id,
                    "status": action.status,
                    "execution_result": action.execution_result,
                    "message": "Action was already successfully executed with this idempotency key.",
                }

            # Check if another action has the same idempotency key
            existing_with_key = (
                db.query(AIAction)
                .filter(AIAction.idempotency_key == idempotency_key, AIAction.id != action.id)
                .first()
            )
            if existing_with_key:
                raise DuplicateExecutionError(
                    f"Idempotency key '{idempotency_key}' was already consumed by action '{existing_with_key.id}'."
                )

            action.idempotency_key = idempotency_key

        # 2. Guardian Compliance Verification
        if not action.guardian_result:
            from backend.app.agents.guardian import GuardianAgent

            guardian_res = GuardianAgent.evaluate_and_apply(db, action)
            if guardian_res.decision == "blocked":
                raise GuardianBlockedError(
                    f"Action cannot be executed because Guardian blocked it: {guardian_res.reason}",
                    details={"guardian_result": action.guardian_result},
                )
            if guardian_res.decision == "requires_approval":
                raise ApprovalRequiredError(
                    f"Action requires explicit merchant approval before execution: {guardian_res.reason}",
                    details={"guardian_result": action.guardian_result},
                )

        if action.status == "blocked":
            raise GuardianBlockedError(
                "Execution rejected: Action is blocked by Guardian policy.",
                details={"guardian_result": action.guardian_result},
            )

        if action.status == "awaiting_approval":
            raise ApprovalRequiredError(
                "Execution rejected: Action is awaiting merchant approval. Call POST /api/actions/approve first.",
                details={"guardian_result": action.guardian_result},
            )

        # 3. Begin Execution Phase
        action.status = "executing"
        db.commit()

        audit_service.record_event(
            db=db,
            merchant_id=action.merchant_id,
            action_id=action.id,
            agent=cls.NAME,
            event_type="EXECUTION_STARTED",
            reason=f"Initiating execution for action type '{action.action_type}'",
            metadata={"payload": action.payload},
        )

        merchant = db.query(Merchant).filter(Merchant.id == action.merchant_id).first()
        currency = merchant.currency if merchant else "INR"
        razorpay = get_razorpay_service()

        try:
            execution_details: Dict[str, Any] = {}
            action_type = action.action_type
            payload = action.payload or {}

            if action_type == "payment_recovery_link":
                amount = float(payload.get("estimated_revenue", 1500.0))
                customer_name = payload.get("customer_name", "Valued Customer")
                customer_email = payload.get("customer_email", "customer@paypilot.demo")
                customer_contact = payload.get("customer_contact", "+919876543210")
                reference_id = f"paypilot_{action.id[-10:]}"

                # Create Razorpay payment link (Test or Mock mode)
                payment_link = razorpay.create_payment_link(
                    amount=amount,
                    currency=currency,
                    customer_name=customer_name,
                    customer_email=customer_email,
                    customer_contact=customer_contact,
                    description=f"PayPilot Payment Recovery - Ref #{action.id[-8:].upper()}",
                    reference_id=reference_id,
                    notes={
                        "action_id": action.id,
                        "opportunity_id": action.opportunity_id or "",
                        "platform": "PayPilot AI Revenue OS",
                    },
                )

                execution_details = {
                    "payment_link_id": payment_link["id"],
                    "short_url": payment_link["short_url"],
                    "reference_id": payment_link["reference_id"],
                    "amount": amount,
                    "amount_paise": payment_link.get("amount"),
                    "currency": currency,
                    "provider": payment_link.get("provider", "razorpay_test"),
                    "status": payment_link.get("status", "created"),
                    "mock": payment_link.get("mock", False),
                    "channel": payload.get("channel", "Automated Razorpay Payment Link"),
                    "targeted_customers": payload.get("customer_count", 1),
                    "timestamp": int(time.time()),
                }

            elif action_type == "winback_discount_campaign":
                budget = float(payload.get("campaign_budget", 3500.0))
                discount = float(payload.get("discount_percent", 10.0))
                sample_amount = float(payload.get("estimated_revenue", budget))
                reference_id = f"paypilot_wb_{action.id[-8:]}"

                # Optionally generate a sample win-back checkout link
                payment_link = razorpay.create_payment_link(
                    amount=sample_amount,
                    currency=currency,
                    customer_name="Win-Back Customer",
                    customer_email="winback@paypilot.demo",
                    description=f"PayPilot Win-Back Incentive ({discount:.0f}% Discount Applied)",
                    reference_id=reference_id,
                    notes={
                        "action_id": action.id,
                        "campaign_type": "winback_discount",
                        "discount_percent": str(discount),
                    },
                )

                execution_details = {
                    "campaign_id": f"cmp_winback_{action.id[-6:]}",
                    "payment_link_id": payment_link.get("id"),
                    "short_url": payment_link.get("short_url"),
                    "reference_id": payment_link.get("reference_id"),
                    "discount_percent": discount,
                    "budget_allocated": budget,
                    "targeted_customers": payload.get("customer_count", 50),
                    "channel": payload.get("channel", "Multi-channel Nudge"),
                    "provider": payment_link.get("provider", "razorpay_test"),
                    "status": "active_campaign",
                    "timestamp": int(time.time()),
                }

            elif action_type == "smart_upsell_nudge":
                discount = float(payload.get("discount_percent", 8.0))
                execution_details = {
                    "upsell_rule_id": f"rule_upsell_{action.id[-6:]}",
                    "discount_percent": discount,
                    "targeted_customers": payload.get("customer_count", 100),
                    "status": "active_nudge",
                    "timestamp": int(time.time()),
                }

            else:
                # Default generic execution handler
                execution_details = {
                    "custom_execution_id": f"exec_custom_{action.id[-6:]}",
                    "action_type": action_type,
                    "status": "completed",
                    "timestamp": int(time.time()),
                }

            # Mark executed successfully
            action.status = "executed"
            action.execution_result = execution_details
            db.commit()
            db.refresh(action)

            provider_label = execution_details.get("provider", "razorpay")
            audit_reason = (
                f"Action '{action.action_type}' executed successfully via {provider_label}. "
                + (f"Payment Link ID: {execution_details.get('payment_link_id')}" if execution_details.get('payment_link_id') else "")
            )

            # Audit event
            audit_service.record_event(
                db=db,
                merchant_id=action.merchant_id,
                action_id=action.id,
                agent=cls.NAME,
                event_type="EXECUTION_SUCCESS",
                reason=audit_reason.strip(),
                metadata=execution_details,
            )

            return {
                "action_id": action.id,
                "status": "executed",
                "execution_result": execution_details,
                "message": "Action executed successfully.",
            }

        except Exception as e:
            action.status = "failed"
            action.execution_result = {"error": str(e)}
            db.commit()

            audit_service.record_event(
                db=db,
                merchant_id=action.merchant_id,
                action_id=action.id,
                agent=cls.NAME,
                event_type="EXECUTION_FAILED",
                reason=f"Execution failed: {str(e)}",
                status="failed",
            )
            raise e
