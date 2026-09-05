import json
import logging
import re
from typing import Dict, Any, List, Optional
import httpx
from pydantic import BaseModel, Field, ValidationError

from backend.app.core.config import settings

logger = logging.getLogger(__name__)


PAYPILOT_SYSTEM_PROMPT = """You are the AI reasoning engine for PayPilot, an AI revenue operating system for merchants.
Your role is ONLY to:
- analyze merchant transaction/customer data
- identify potential revenue opportunities
- explain evidence
- estimate opportunity confidence (0.0 to 1.0)
- recommend possible actions and recovery strategies

You MUST NOT:
- directly execute payments
- directly create Razorpay payment links
- bypass Guardian
- change financial policies
- approve your own actions
- make final authorization decisions
- invent transaction/customer facts not present in the supplied data

Financial safety rules remain strictly deterministic in the Guardian service.
You are an advisory and reasoning component, not the execution authority.

You MUST respond with a valid JSON object strictly matching this schema:
{
  "summary": "1-2 sentence executive analytical synthesis of why this opportunity exists",
  "key_factors": ["factor 1", "factor 2", "factor 3"],
  "recommended_action": "payment_recovery_link" | "winback_discount_campaign" | "smart_upsell_nudge" | "recurring_mandate_refresh",
  "confidence": 0.0 to 1.0,
  "risk": "low" | "medium" | "high",
  "expected_recovery": number,
  "risk_factors": ["risk factor 1"]
}
Do NOT wrap the JSON in conversational banter. Return ONLY valid JSON."""


class LLMReasoningOutput(BaseModel):
    """Structured JSON schema for LLM opportunity reasoning."""
    summary: str = Field(..., description="Human-readable synthesis of why this revenue opportunity exists")
    key_factors: List[str] = Field(default_factory=list, description="2-4 bullet points highlighting supporting data")
    recommended_action: str = Field(..., description="Tactical action name or recommendation")
    confidence: float = Field(default=0.85, ge=0.0, le=1.0, description="Model confidence score")
    risk: str = Field(default="low", description="Risk assessment: low, medium, or high")
    expected_recovery: Optional[float] = Field(default=None, description="Estimated recoverable revenue")
    risk_factors: Optional[List[str]] = Field(default_factory=list, description="Specific risk indicators")


def extract_json_from_text(raw_text: str) -> Optional[Dict[str, Any]]:
    """
    Robustly extract and parse JSON object from LLM response.
    Handles raw JSON, markdown code blocks (```json ... ```), and embedded JSON strings.
    """
    if not raw_text or not isinstance(raw_text, str):
        return None

    cleaned = raw_text.strip()

    # 1. Direct JSON parse
    try:
        data = json.loads(cleaned)
        if isinstance(data, dict):
            return data
    except json.JSONDecodeError:
        pass

    # 2. Markdown code fence extraction: ```json { ... } ``` or ``` { ... } ```
    fence_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
    match = re.search(fence_pattern, cleaned, re.DOTALL)
    if match:
        try:
            data = json.loads(match.group(1).strip())
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass

    # 3. First '{' to last '}' extraction
    first_brace = cleaned.find("{")
    last_brace = cleaned.rfind("}")
    if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
        json_slice = cleaned[first_brace : last_brace + 1]
        try:
            data = json.loads(json_slice)
            if isinstance(data, dict):
                return data
        except json.JSONDecodeError:
            pass

    return None


class OllamaService:
    """
    Isolated service communicating with local Ollama HTTP API.
    Provides structured opportunity reasoning, text generation, and connectivity health probes.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL
        self.timeout = timeout or settings.OLLAMA_TIMEOUT_SECONDS

    def health_check(self) -> Dict[str, Any]:
        """
        Probe local Ollama daemon connectivity and verify configured model availability.
        """
        url = f"{self.base_url}/api/tags"
        try:
            with httpx.Client(timeout=1.5) as client:
                resp = client.get(url)
                if resp.status_code == 200:
                    payload = resp.json()
                    models = [m.get("name", "") for m in payload.get("models", [])]
                    is_model_present = any(
                        self.model in m or m.startswith(self.model.split(":")[0])
                        for m in models
                    )
                    return {
                        "status": "connected",
                        "provider": "ollama",
                        "model": self.model,
                        "model_available": is_model_present,
                        "available_models": models,
                        "base_url": self.base_url,
                    }
        except Exception as e:
            logger.debug(f"Ollama health probe offline: {type(e).__name__}: {str(e)}")

        return {
            "status": "unavailable",
            "provider": "ollama",
            "model": self.model,
            "model_available": False,
            "available_models": [],
            "base_url": self.base_url,
        }

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.2,
    ) -> Optional[str]:
        """
        Send a generation request to the local Ollama HTTP API.
        """
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system or PAYPILOT_SYSTEM_PROMPT,
            "format": "json",
            "stream": False,
            "options": {
                "temperature": temperature,
            },
        }

        logger.info(f"Ollama request started -> model='{self.model}' at {self.base_url}")

        try:
            with httpx.Client(timeout=self.timeout) as client:
                resp = client.post(url, json=payload)
                if resp.status_code == 200:
                    res_json = resp.json()
                    raw_response = res_json.get("response", "")
                    logger.info(f"Ollama response received successfully ({len(raw_response)} chars).")
                    return raw_response
                else:
                    logger.warning(
                        f"Ollama HTTP error status {resp.status_code}: {resp.text}"
                    )
                    return None
        except httpx.TimeoutException:
            logger.warning(f"Ollama request timed out after {self.timeout}s.")
            return None
        except httpx.ConnectError:
            logger.warning(f"Ollama daemon unavailable at {self.base_url}.")
            return None
        except Exception as e:
            logger.warning(f"Ollama request failed ({type(e).__name__}: {str(e)}).")
            return None

    def analyze_opportunity(
        self, opportunity_type: str, context: Dict[str, Any]
    ) -> Optional[LLMReasoningOutput]:
        """
        Perform structured reasoning on an opportunity candidate using Ollama.
        Returns parsed LLMReasoningOutput or None on failure.
        """
        sanitized_context = {
            "opportunity_type": opportunity_type,
            "potential_revenue_inr": float(context.get("potential_revenue", 0.0)),
            "affected_customer_count": int(context.get("customer_count", 0)),
            "statistical_confidence": float(context.get("confidence", 0.85)),
            "assessed_risk": str(context.get("risk", "low")),
            "suggested_action": str(context.get("recommended_action", "payment_recovery_link")),
            "lookback_hours": context.get("lookback_hours", 72),
            "recent_failures_count": context.get("recent_failures_count"),
            "dormant_days": context.get("dormant_days"),
            "avg_ltv": context.get("avg_ltv"),
            "avg_repeat_prob": context.get("avg_repeat_prob"),
            "target_category": context.get("target_category"),
        }

        # Filter out None values
        sanitized_context = {k: v for k, v in sanitized_context.items() if v is not None}

        user_prompt = f"""Merchant Opportunity Candidate Data:
{json.dumps(sanitized_context, indent=2)}

Please evaluate this opportunity and provide your structured analytical rationale in JSON format."""

        raw_response = self.generate(
            prompt=user_prompt,
            system=PAYPILOT_SYSTEM_PROMPT,
            temperature=0.2,
        )

        if not raw_response:
            return None

        parsed_dict = extract_json_from_text(raw_response)
        if not parsed_dict:
            logger.warning(f"Failed to parse valid JSON from Ollama output: {raw_response[:200]}")
            return None

        try:
            # Normalize fields if necessary
            confidence = parsed_dict.get("confidence", context.get("confidence", 0.85))
            try:
                confidence = float(confidence)
                confidence = max(0.0, min(1.0, confidence))
            except (ValueError, TypeError):
                confidence = float(context.get("confidence", 0.85))

            return LLMReasoningOutput(
                summary=str(parsed_dict.get("summary", "")).strip(),
                key_factors=list(parsed_dict.get("key_factors", [])),
                recommended_action=str(parsed_dict.get("recommended_action", sanitized_context.get("suggested_action", ""))).strip(),
                confidence=confidence,
                risk=str(parsed_dict.get("risk", "low")).lower(),
                expected_recovery=parsed_dict.get("expected_recovery"),
                risk_factors=list(parsed_dict.get("risk_factors", [])),
            )
        except ValidationError as ve:
            logger.warning(f"Ollama JSON schema validation failed: {ve}")
            return None


# Global singleton instance
ollama_service = OllamaService()
