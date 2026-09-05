from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import json
import logging
from pydantic import BaseModel, Field, ValidationError

from backend.app.core.config import settings
from backend.app.services.ollama_service import (
    ollama_service,
    OllamaService,
    LLMReasoningOutput,
)

logger = logging.getLogger(__name__)


class ReasoningResult(BaseModel):
    """Standardized output container containing explanation and source attribution."""
    explanation: str
    reasoning_source: str = "deterministic"  # "ollama", "openai", or "deterministic_fallback"
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


class OllamaReasoningEngine(ReasoningEngine):
    """
    Ollama LLM reasoning engine.
    Communicates with local Ollama daemon (e.g. gemma4:latest, qwen3.6:27b).
    Produces rich natural language synthesis and key analytical drivers with automatic
    deterministic fallback on connectivity drop, timeout, or malformed model output.
    """

    def __init__(
        self,
        service: Optional[OllamaService] = None,
        fallback_engine: Optional[ReasoningEngine] = None,
    ):
        self.service = service or ollama_service
        self.fallback = fallback_engine or DeterministicReasoningEngine()

    def generate_opportunity_reasoning(
        self, opportunity_type: str, context: Dict[str, Any]
    ) -> ReasoningResult:
        """
        Generate structured opportunity reasoning using Ollama with deterministic fallback.
        """
        try:
            logger.info(
                f"Invoking Ollama reasoning engine for opportunity '{opportunity_type}'..."
            )
            output: Optional[LLMReasoningOutput] = self.service.analyze_opportunity(
                opportunity_type=opportunity_type,
                context=context,
            )

            if output and output.summary:
                logger.info(
                    f"Ollama reasoning generated successfully for '{opportunity_type}' (confidence: {output.confidence:.2f})."
                )
                revenue = float(context.get("potential_revenue", 0.0))
                customer_count = int(context.get("customer_count", 0))

                key_factors = output.key_factors
                if not key_factors:
                    key_factors = [
                        f"{customer_count} verified customer accounts in cohort",
                        f"₹{revenue:,.0f} calculated revenue potential",
                        f"{int(output.confidence * 100)}% model confidence",
                    ]

                return ReasoningResult(
                    explanation=output.summary,
                    reasoning_source="ollama",
                    key_factors=key_factors,
                    recommended_action=output.recommended_action or str(context.get("recommended_action", "payment_recovery_link")),
                    confidence=output.confidence,
                    risk=output.risk,
                )
            else:
                logger.warning(
                    f"Ollama reasoning returned empty/unusable output. Activating deterministic fallback."
                )
        except Exception as e:
            logger.warning(
                f"Ollama reasoning error ({type(e).__name__}: {str(e)}). Activating deterministic fallback."
            )

        # Execute fallback
        fallback_result = self.fallback.generate_opportunity_reasoning(opportunity_type, context)
        fallback_result.reasoning_source = "deterministic_fallback"
        return fallback_result

    def explain_opportunity(self, opportunity_type: str, context: Dict[str, Any]) -> str:
        result = self.generate_opportunity_reasoning(opportunity_type, context)
        return result.explanation

    def explain_recommended_action(self, action_type: str, context: Dict[str, Any]) -> str:
        return self.fallback.explain_recommended_action(action_type, context)

    def explain_guardian_decision(self, decision: str, policy_violations: List[str], context: Dict[str, Any]) -> str:
        return self.fallback.explain_guardian_decision(decision, policy_violations, context)


class OpenAIReasoningEngine(ReasoningEngine):
    """
    OpenAI LLM-based reasoning engine (Alternative provider).
    """

    def __init__(self, fallback_engine: Optional[ReasoningEngine] = None):
        self.fallback = fallback_engine or DeterministicReasoningEngine()

    def generate_opportunity_reasoning(self, opportunity_type: str, context: Dict[str, Any]) -> ReasoningResult:
        if not settings.OPENAI_API_KEY:
            logger.info("OpenAI API key not configured. Using deterministic reasoning engine.")
            return self.fallback.generate_opportunity_reasoning(opportunity_type, context)

        try:
            import openai

            client = openai.OpenAI(
                api_key=settings.OPENAI_API_KEY,
                timeout=settings.LLM_TIMEOUT_SECONDS,
            )

            user_prompt = f"Opportunity Data:\n{json.dumps(context, indent=2)}"

            response = client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are PayPilot's AI Analyst. Return JSON matching summary, key_factors, recommended_action, confidence, risk."},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )

            raw_content = response.choices[0].message.content or "{}"
            parsed = LLMReasoningOutput.model_validate_json(raw_content)

            return ReasoningResult(
                explanation=parsed.summary,
                reasoning_source="openai",
                key_factors=parsed.key_factors,
                recommended_action=parsed.recommended_action or str(context.get("recommended_action", "")),
                confidence=parsed.confidence,
                risk=parsed.risk,
            )

        except Exception as e:
            logger.warning(f"OpenAI LLM failed ({type(e).__name__}: {str(e)}). Falling back to deterministic engine.")
            fallback_res = self.fallback.generate_opportunity_reasoning(opportunity_type, context)
            fallback_res.reasoning_source = "deterministic_fallback"
            return fallback_res

    def explain_opportunity(self, opportunity_type: str, context: Dict[str, Any]) -> str:
        result = self.generate_opportunity_reasoning(opportunity_type, context)
        return result.explanation

    def explain_recommended_action(self, action_type: str, context: Dict[str, Any]) -> str:
        return self.fallback.explain_recommended_action(action_type, context)

    def explain_guardian_decision(self, decision: str, policy_violations: List[str], context: Dict[str, Any]) -> str:
        return self.fallback.explain_guardian_decision(decision, policy_violations, context)


class DynamicReasoningEngine(ReasoningEngine):
    """Dynamic proxy that delegates calls to the currently configured engine based on settings.LLM_PROVIDER."""

    def explain_opportunity(self, opportunity_type: str, context: Dict[str, Any]) -> str:
        return get_reasoning_engine().explain_opportunity(opportunity_type, context)

    def generate_opportunity_reasoning(self, opportunity_type: str, context: Dict[str, Any]) -> ReasoningResult:
        return get_reasoning_engine().generate_opportunity_reasoning(opportunity_type, context)

    def explain_recommended_action(self, action_type: str, context: Dict[str, Any]) -> str:
        return get_reasoning_engine().explain_recommended_action(action_type, context)

    def explain_guardian_decision(self, decision: str, policy_violations: List[str], context: Dict[str, Any]) -> str:
        return get_reasoning_engine().explain_guardian_decision(decision, policy_violations, context)


def get_reasoning_engine() -> ReasoningEngine:
    """Factory to instantiate configured reasoning engine."""
    deterministic = DeterministicReasoningEngine()
    if settings.LLM_PROVIDER == "ollama":
        return OllamaReasoningEngine(service=ollama_service, fallback_engine=deterministic)
    elif settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
        return OpenAIReasoningEngine(fallback_engine=deterministic)
    return deterministic


# Global dynamic reasoning service instance
reasoning_service: ReasoningEngine = DynamicReasoningEngine()
