from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import json
import logging
from pydantic import BaseModel, Field, ValidationError
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class LLMReasoningOutput(BaseModel):
    """Strict JSON schema expected from LLM reasoning response."""
    summary: str = Field(..., description="Human-readable synthesis of why this revenue opportunity exists")
    key_factors: List[str] = Field(default_factory=list, description="2-4 bullet points highlighting supporting data")
    recommended_action: str = Field(..., description="Tactical action name or recommendation")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence score")
    risk: str = Field(default="low", description="Risk assessment: low, medium, or high")


class ReasoningResult(BaseModel):
    """Standardized output container containing explanation and source attribution."""
    explanation: str
    reasoning_source: str = "deterministic"  # "llm" or "deterministic"
    key_factors: List[str] = Field(default_factory=list)
    recommended_action: str
    confidence: float
    risk: str


class ReasoningEngine(ABC):
    """Abstract interface for PayPilot AI reasoning layer."""

    @abstractmethod
    def explain_opportunity(self, opportunity_type: str, context: Dict[str, Any]) -> str:
        """Generate human-readable justification for an opportunity."""
        pass

    @abstractmethod
    def generate_opportunity_reasoning(self, opportunity_type: str, context: Dict[str, Any]) -> ReasoningResult:
        """Generate full structured reasoning result with source attribution."""
        pass

    @abstractmethod
    def explain_recommended_action(self, action_type: str, context: Dict[str, Any]) -> str:
        """Generate explanation for why a specific action is recommended."""
        pass

    @abstractmethod
    def explain_guardian_decision(self, decision: str, policy_violations: List[str], context: Dict[str, Any]) -> str:
        """Explain Guardian policy decision in plain language."""
        pass


class DeterministicReasoningEngine(ReasoningEngine):
    """Deterministic, rule-based reasoning engine with statistical calculations."""

    def explain_opportunity(self, opportunity_type: str, context: Dict[str, Any]) -> str:
        currency_symbol = context.get("currency_symbol", "₹")
        revenue = float(context.get("potential_revenue", 0.0))
        customer_count = int(context.get("customer_count", 0))
        formatted_revenue = f"{currency_symbol}{revenue:,.0f}"

        if opportunity_type == "payment_recovery":
            hours = context.get("lookback_hours", 72)
            retry_count = context.get("recent_failures_count", customer_count)
            return (
                f"{customer_count} customers experienced payment failure within the last {hours} hours, "
                f"representing {formatted_revenue} in potentially recoverable revenue across {retry_count} failed attempts."
            )

        elif opportunity_type == "customer_winback":
            dormant_days = context.get("dormant_days", 45)
            avg_ltv = float(context.get("avg_ltv", 0.0))
            formatted_ltv = f"{currency_symbol}{avg_ltv:,.0f}"
            return (
                f"{customer_count} previously active high-value customers (avg. LTV {formatted_ltv}) "
                f"have lapsed beyond their typical {dormant_days}-day reorder window, representing {formatted_revenue} in at-risk revenue."
            )

        elif opportunity_type == "upsell":
            repeat_prob = int(float(context.get("avg_repeat_prob", 0.82)) * 100)
            category = context.get("target_category", "complementary categories")
            return (
                f"{customer_count} repeat customers with >{repeat_prob}% purchase affinity show strong propensity "
                f"for upsell in {category}, with estimated incremental value of {formatted_revenue}."
            )

        elif opportunity_type == "subscription_recovery":
            cycles = context.get("failed_cycles", 1)
            return (
                f"{customer_count} active subscriber accounts experienced recurring billing drop-off ({cycles} missed cycles), "
                f"representing {formatted_revenue} in immediate recurring cash flow."
            )

        return (
            f"Identified {customer_count} customer touchpoints with {formatted_revenue} in potential revenue impact."
        )

    def generate_opportunity_reasoning(self, opportunity_type: str, context: Dict[str, Any]) -> ReasoningResult:
        explanation = self.explain_opportunity(opportunity_type, context)
        revenue = float(context.get("potential_revenue", 0.0))
        customer_count = int(context.get("customer_count", 0))
        confidence = float(context.get("confidence", 0.85))
        risk = str(context.get("risk", "low"))
        rec_action = str(context.get("recommended_action", "payment_recovery_link"))

        key_factors = [
            f"{customer_count} accounts identified in cohort",
            f"₹{revenue:,.0f} estimated revenue opportunity",
            f"{int(confidence * 100)}% statistical model confidence",
        ]

        return ReasoningResult(
            explanation=explanation,
            reasoning_source="deterministic",
            key_factors=key_factors,
            recommended_action=rec_action,
            confidence=confidence,
            risk=risk,
        )

    def explain_recommended_action(self, action_type: str, context: Dict[str, Any]) -> str:
        discount = context.get("discount_percent", 0)
        channel = context.get("channel", "Automated Smart Link / WhatsApp / SMS")
        action_title = context.get("action_title", action_type)

        if action_type == "payment_recovery_link":
            return (
                f"Dispatch dynamic 1-click Razorpay payment recovery links via {channel} with intelligent checkout retries."
            )
        elif action_type == "winback_discount_campaign":
            return (
                f"Launch a personalized win-back sequence offering an exclusive {discount}% incentive to re-engage lapsed buyers."
            )
        elif action_type == "smart_upsell_nudge":
            return (
                f"Send tailored product bundle recommendations featuring complementary high-margin inventory."
            )
        elif action_type == "recurring_mandate_refresh":
            return (
                f"Trigger an automated mandate re-authentication flow with fallback UPI/card authorization."
            )

        return f"Execute {action_title} across targeted customer cohort."

    def explain_guardian_decision(self, decision: str, policy_violations: List[str], context: Dict[str, Any]) -> str:
        if decision == "approved":
            return "Action strictly complies with all merchant-configured financial guardrails and risk thresholds."
        elif decision == "blocked":
            reasons = "; ".join(policy_violations)
            return f"Action was blocked by Guardian policy: {reasons}"
        elif decision == "requires_approval":
            amount = float(context.get("estimated_amount", 0.0))
            threshold = float(context.get("approval_threshold", 5000.0))
            return (
                f"Action exceeds autonomous financial threshold of ₹{threshold:,.0f} (estimated impact: ₹{amount:,.0f}). "
                f"Explicit merchant sign-off is required before execution."
            )
        return f"Guardian evaluation completed with status: {decision}."


class OpenAIReasoningEngine(ReasoningEngine):
    """
    OpenAI LLM-based reasoning engine.
    Produces rich natural language synthesis and key analytical drivers with automatic
    fallback to DeterministicReasoningEngine on missing API key, timeouts, or API errors.
    """

    def __init__(self, fallback_engine: Optional[ReasoningEngine] = None):
        self.fallback = fallback_engine or DeterministicReasoningEngine()

    def _sanitize_llm_input(self, opportunity_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Construct a minimal, privacy-safe structural payload for the LLM.
        Strips all PII, secrets, credentials, and raw database identifiers.
        """
        evidence_list = []
        if opportunity_type == "payment_recovery":
            evidence_list = [
                f"{context.get('customer_count', 0)} recent failed payments",
                "Customers have established prior purchasing history",
                f"Failures occurred within the last {context.get('lookback_hours', 72)} hours",
            ]
        elif opportunity_type == "customer_winback":
            evidence_list = [
                f"{context.get('customer_count', 0)} lapsed accounts with positive LTV",
                f"Inactive beyond typical {context.get('dormant_days', 45)}-day reorder cycle",
            ]
        elif opportunity_type == "upsell":
            evidence_list = [
                f"{context.get('customer_count', 0)} multi-order repeat buyers",
                f"Propensity score: {context.get('avg_repeat_prob', 0.82)}",
                f"Catalog match in {context.get('target_category', 'accessories')}",
            ]
        else:
            evidence_list = [
                f"{context.get('customer_count', 0)} affected subscriber accounts",
                "Recurring billing mandate drop-off detected",
            ]

        return {
            "opportunity_type": opportunity_type,
            "potential_revenue_inr": float(context.get("potential_revenue", 0.0)),
            "affected_customers": int(context.get("customer_count", 0)),
            "model_confidence": float(context.get("confidence", 0.85)),
            "assessed_risk": str(context.get("risk", "low")),
            "recommended_action": str(context.get("recommended_action", "payment_recovery_link")),
            "evidence": evidence_list,
        }

    def generate_opportunity_reasoning(self, opportunity_type: str, context: Dict[str, Any]) -> ReasoningResult:
        # Check if API key is present
        if not settings.OPENAI_API_KEY or settings.LLM_PROVIDER != "openai":
            logger.info("OpenAI API key not configured. Using deterministic reasoning engine.")
            return self.fallback.generate_opportunity_reasoning(opportunity_type, context)

        try:
            import openai

            client = openai.OpenAI(
                api_key=settings.OPENAI_API_KEY,
                timeout=settings.LLM_TIMEOUT_SECONDS,
            )

            sanitized_input = self._sanitize_llm_input(opportunity_type, context)

            system_prompt = (
                "You are PayPilot's AI Analyst Agent for merchant revenue optimization.\n"
                "Analyze the opportunity metrics and generate a concise, explainable rationale.\n"
                "Return a valid JSON object strictly matching this schema:\n"
                "{\n"
                '  "summary": "1-2 sentence executive summary of why this opportunity exists",\n'
                '  "key_factors": ["factor 1", "factor 2", "factor 3"],\n'
                '  "recommended_action": "name of recommended action",\n'
                '  "confidence": 0.0 to 1.0,\n'
                '  "risk": "low" | "medium" | "high"\n'
                "}"
            )

            user_prompt = f"Opportunity Data:\n{json.dumps(sanitized_input, indent=2)}"

            response = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )

            raw_content = response.choices[0].message.content or "{}"
            parsed = LLMReasoningOutput.model_validate_json(raw_content)

            return ReasoningResult(
                explanation=parsed.summary,
                reasoning_source="llm",
                key_factors=parsed.key_factors or [
                    f"{sanitized_input['affected_customers']} customers in cohort",
                    f"₹{sanitized_input['potential_revenue_inr']:,.0f} revenue potential",
                ],
                recommended_action=parsed.recommended_action or sanitized_input["recommended_action"],
                confidence=parsed.confidence,
                risk=parsed.risk,
            )

        except Exception as e:
            logger.warning(f"LLM reasoning failed ({type(e).__name__}: {str(e)}). Falling back to deterministic engine.")
            return self.fallback.generate_opportunity_reasoning(opportunity_type, context)

    def explain_opportunity(self, opportunity_type: str, context: Dict[str, Any]) -> str:
        result = self.generate_opportunity_reasoning(opportunity_type, context)
        return result.explanation

    def explain_recommended_action(self, action_type: str, context: Dict[str, Any]) -> str:
        return self.fallback.explain_recommended_action(action_type, context)

    def explain_guardian_decision(self, decision: str, policy_violations: List[str], context: Dict[str, Any]) -> str:
        return self.fallback.explain_guardian_decision(decision, policy_violations, context)


def get_reasoning_engine() -> ReasoningEngine:
    """Factory to instantiate configured reasoning engine."""
    deterministic = DeterministicReasoningEngine()
    if settings.OPENAI_API_KEY and settings.LLM_PROVIDER == "openai":
        return OpenAIReasoningEngine(fallback_engine=deterministic)
    return deterministic


# Global reasoning service instance
reasoning_service: ReasoningEngine = OpenAIReasoningEngine(fallback_engine=DeterministicReasoningEngine())
