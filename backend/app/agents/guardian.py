from sqlalchemy.orm import Session
from backend.app.models.ai_action import AIAction
from backend.app.services.guardian_service import guardian_service
from backend.app.services.audit_service import audit_service
from backend.app.schemas.guardian import GuardianEvaluationResult


class GuardianAgent:
    """
    GUARDIAN AGENT:
    Deterministic financial guardian and policy gatekeeper.
    Enforces merchant-defined constraints and decides if actions can proceed autonomously.
    """

    NAME = "guardian"

    @classmethod
    def evaluate_and_apply(cls, db: Session, action: AIAction) -> GuardianEvaluationResult:
        estimated_amount = action.payload.get("estimated_cost", action.payload.get("campaign_budget", 0.0))

        result = guardian_service.evaluate_action(
            db=db,
            merchant_id=action.merchant_id,
            action_payload=action.payload,
            confidence=action.confidence,
            estimated_amount=estimated_amount,
        )

        action.guardian_result = result.model_dump()

        if result.decision == "approved":
            action.status = "approved"
            event_type = "GUARDIAN_APPROVED"
        elif result.decision == "blocked":
            action.status = "blocked"
            event_type = "GUARDIAN_BLOCKED"
        elif result.decision == "requires_approval":
            action.status = "awaiting_approval"
            event_type = "GUARDIAN_FLAGGED_FOR_APPROVAL"
        else:
            action.status = "blocked"
            event_type = "GUARDIAN_BLOCKED"

        db.commit()
        db.refresh(action)

        # Audit event
        audit_service.record_event(
            db=db,
            merchant_id=action.merchant_id,
            action_id=action.id,
            agent=cls.NAME,
            event_type=event_type,
            reason=result.reason,
            metadata={
                "decision": result.decision,
                "risk_level": result.risk_level,
                "policy_checks": [c.model_dump() for c in result.policy_checks],
            },
        )

        return result
