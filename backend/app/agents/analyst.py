from typing import Dict, Any
from sqlalchemy.orm import Session
from backend.app.models.opportunity import Opportunity
from backend.app.services.audit_service import audit_service
from backend.app.services.reasoning_service import reasoning_service


class AnalystAgent:
    """
    ANALYST AGENT:
    Enriches opportunities with empirical revenue estimations, confidence metrics,
    risk profiles, LLM reasoning synthesis, and structured supporting evidence.
    """

    NAME = "analyst"

    @classmethod
    def analyze_opportunity(cls, db: Session, opportunity: Opportunity) -> Dict[str, Any]:
        # Invoke reasoning service (OpenAI LLM with automatic deterministic fallback)
        reasoning_result = reasoning_service.generate_opportunity_reasoning(
            opportunity_type=opportunity.type,
            context={
                "potential_revenue": opportunity.potential_revenue,
                "customer_count": opportunity.affected_customer_count,
                "confidence": opportunity.confidence,
                "risk": opportunity.risk,
                "recommended_action": opportunity.recommended_action,
            },
        )

        analysis_data = {
            "opportunity_id": opportunity.id,
            "merchant_id": opportunity.merchant_id,
            "type": opportunity.type,
            "potential_revenue": opportunity.potential_revenue,
            "confidence": opportunity.confidence,
            "risk": opportunity.risk,
            "affected_customer_count": opportunity.affected_customer_count,
            "reason": reasoning_result.explanation,
            "reasoning": reasoning_result.explanation,
            "reasoning_source": reasoning_result.reasoning_source,
            "key_factors": reasoning_result.key_factors,
            "recommended_action": opportunity.recommended_action,
            "supporting_evidence": {
                "metric_basis": f"Cohort analysis over {opportunity.affected_customer_count} verified accounts.",
                "reasoning_source": reasoning_result.reasoning_source,
                "key_factors": reasoning_result.key_factors,
                "data_points": [
                    {"label": "Potential Revenue", "value": f"₹{opportunity.potential_revenue:,.0f}"},
                    {"label": "Target Cohort", "value": f"{opportunity.affected_customer_count} customers"},
                    {"label": "Model Confidence", "value": f"{opportunity.confidence * 100:.1f}%"},
                    {"label": "Assessed Risk", "value": opportunity.risk.upper()},
                    {"label": "Reasoning Engine", "value": reasoning_result.reasoning_source.upper()},
                ],
            },
        }

        # Update status if discovered
        if opportunity.status == "discovered":
            opportunity.status = "analyzed"
            db.commit()
            db.refresh(opportunity)

            # Record audit event
            audit_service.record_event(
                db=db,
                merchant_id=opportunity.merchant_id,
                agent=cls.NAME,
                event_type="OPPORTUNITY_ANALYZED",
                reason=f"Analyst evaluated {opportunity.type} via {reasoning_result.reasoning_source} engine.",
                metadata={
                    "opportunity_id": opportunity.id,
                    "confidence": opportunity.confidence,
                    "potential_revenue": opportunity.potential_revenue,
                    "reasoning_source": reasoning_result.reasoning_source,
                },
            )

        return analysis_data
