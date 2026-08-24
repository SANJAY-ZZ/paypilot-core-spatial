from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from backend.app.models.opportunity import Opportunity
from backend.app.models.ai_action import AIAction
from backend.app.services.reasoning_service import reasoning_service
from backend.app.services.audit_service import audit_service


class StrategistAgent:
    """
    STRATEGIST AGENT:
    Selects optimal execution strategies and packages structured action payloads.
    Strategist proposes actions; it does not execute them.
    """

    NAME = "strategist"

    @classmethod
    def propose_action(
        cls,
        db: Session,
        opportunity: Opportunity,
        override_discount_percent: Optional[float] = None,
        override_budget: Optional[float] = None,
        target_customer_ids: Optional[List[str]] = None,
    ) -> AIAction:
        action_type = opportunity.recommended_action

        # Default strategy parameters based on opportunity type
        if opportunity.type == "payment_recovery":
            discount_percent = override_discount_percent if override_discount_percent is not None else 0.0
            budget = override_budget if override_budget is not None else 500.0  # WhatsApp/SMS dispatch cost
            estimated_revenue = opportunity.potential_revenue
            estimated_cost = budget + (estimated_revenue * (discount_percent / 100.0))
            channel = "Razorpay Smart Links + Automated WhatsApp/Email"
            action_name = "payment_recovery_link"

        elif opportunity.type == "customer_winback":
            discount_percent = override_discount_percent if override_discount_percent is not None else 12.0
            budget = override_budget if override_budget is not None else 3500.0
            estimated_revenue = opportunity.potential_revenue
            estimated_cost = budget + (estimated_revenue * (discount_percent / 100.0))
            channel = "Personalized Win-Back Incentive via Multi-Channel Nudge"
            action_name = "winback_discount_campaign"

        elif opportunity.type == "upsell":
            discount_percent = override_discount_percent if override_discount_percent is not None else 8.0
            budget = override_budget if override_budget is not None else 2000.0
            estimated_revenue = opportunity.potential_revenue
            estimated_cost = budget + (estimated_revenue * (discount_percent / 100.0))
            channel = "Algorithmic Cross-Sell Recommendation on Checkout & Post-Purchase"
            action_name = "smart_upsell_nudge"

        elif opportunity.type == "subscription_recovery":
            discount_percent = override_discount_percent if override_discount_percent is not None else 0.0
            budget = override_budget if override_budget is not None else 1000.0
            estimated_revenue = opportunity.potential_revenue
            estimated_cost = budget
            channel = "Automated Recurring Mandate Sync & Re-Auth"
            action_name = "recurring_mandate_refresh"

        else:
            discount_percent = override_discount_percent if override_discount_percent is not None else 5.0
            budget = override_budget if override_budget is not None else 1000.0
            estimated_revenue = opportunity.potential_revenue
            estimated_cost = budget
            channel = "Direct Merchant Notification"
            action_name = action_type

        strategy_reason = reasoning_service.explain_recommended_action(
            action_name,
            {
                "discount_percent": discount_percent,
                "channel": channel,
                "action_title": opportunity.title,
            },
        )

        payload = {
            "action_name": action_name,
            "opportunity_type": opportunity.type,
            "discount_percent": discount_percent,
            "campaign_budget": budget,
            "customer_count": opportunity.affected_customer_count,
            "target_customer_ids": target_customer_ids or [],
            "estimated_revenue": round(estimated_revenue, 2),
            "estimated_cost": round(estimated_cost, 2),
            "channel": channel,
            "strategy_reason": strategy_reason,
            "suggested_expiry_hours": 48,
        }

        # Create proposed AIAction
        action = AIAction(
            merchant_id=opportunity.merchant_id,
            opportunity_id=opportunity.id,
            agent=cls.NAME,
            action_type=action_name,
            payload=payload,
            confidence=opportunity.confidence,
            status="proposed",
            guardian_result=None,
            execution_result=None,
        )

        db.add(action)
        db.commit()
        db.refresh(action)

        # Update opportunity state
        opportunity.status = "action_proposed"
        db.commit()

        # Audit event
        audit_service.record_event(
            db=db,
            merchant_id=opportunity.merchant_id,
            agent=cls.NAME,
            action_id=action.id,
            event_type="ACTION_PROPOSED",
            reason=f"Strategist proposed action '{action_name}' for opportunity '{opportunity.title}'",
            metadata={
                "action_id": action.id,
                "action_type": action_name,
                "estimated_revenue": estimated_revenue,
                "estimated_cost": estimated_cost,
                "discount_percent": discount_percent,
            },
        )

        return action
