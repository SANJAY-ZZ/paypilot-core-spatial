import json
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.services.reasoning_service import (
    DeterministicReasoningEngine,
    OpenAIReasoningEngine,
    LLMReasoningOutput,
)
from backend.app.models.merchant import Merchant
from backend.app.models.opportunity import Opportunity
from backend.app.agents.analyst import AnalystAgent
from backend.app.agents.strategist import StrategistAgent
from backend.app.agents.guardian import GuardianAgent


def test_llm_fallback_when_api_key_missing():
    """Test automatic fallback to deterministic engine when OPENAI_API_KEY is unset."""
    with patch.object(settings, "OPENAI_API_KEY", ""):
        engine = OpenAIReasoningEngine()
        context = {
            "potential_revenue": 38400.0,
            "customer_count": 23,
            "confidence": 0.94,
            "risk": "low",
            "recommended_action": "payment_recovery_link",
        }
        res = engine.generate_opportunity_reasoning("payment_recovery", context)
        assert res.reasoning_source == "deterministic"
        assert "23 customers" in res.explanation
        assert len(res.key_factors) > 0


def test_successful_structured_llm_reasoning():
    """Test OpenAI reasoning engine parsing structured JSON output correctly."""
    mock_llm_response = json.dumps({
        "summary": "23 customers experienced recent checkout drops and possess solid transaction history, making them prime candidates for automated recovery.",
        "key_factors": [
            "23 verified payment drop-offs within 72 hours",
            "Strong historical transaction affinity",
            "₹38,400 immediate recoverable cashflow",
        ],
        "recommended_action": "payment_recovery_link",
        "confidence": 0.94,
        "risk": "low",
    })

    with patch.object(settings, "OPENAI_API_KEY", "sk-mock-key-12345"):
        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_completion = MagicMock()
            mock_completion.choices = [MagicMock(message=MagicMock(content=mock_llm_response))]
            mock_client.chat.completions.create.return_value = mock_completion

            engine = OpenAIReasoningEngine()
            context = {
                "potential_revenue": 38400.0,
                "customer_count": 23,
                "confidence": 0.94,
                "risk": "low",
                "recommended_action": "payment_recovery_link",
            }
            res = engine.generate_opportunity_reasoning("payment_recovery", context)

            assert res.reasoning_source == "llm"
            assert "prime candidates for automated recovery" in res.explanation
            assert len(res.key_factors) == 3
            assert res.confidence == 0.94
            assert res.risk == "low"


def test_malformed_llm_json_fallback():
    """Test that malformed JSON from the LLM automatically triggers deterministic fallback."""
    with patch.object(settings, "OPENAI_API_KEY", "sk-mock-key-12345"):
        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_completion = MagicMock()
            # Return invalid non-JSON string
            mock_completion.choices = [MagicMock(message=MagicMock(content="Here is some non-json text"))]
            mock_client.chat.completions.create.return_value = mock_completion

            engine = OpenAIReasoningEngine()
            context = {
                "potential_revenue": 38400.0,
                "customer_count": 23,
                "confidence": 0.94,
                "risk": "low",
                "recommended_action": "payment_recovery_link",
            }
            res = engine.generate_opportunity_reasoning("payment_recovery", context)

            assert res.reasoning_source == "deterministic"
            assert "23 customers experienced payment failure" in res.explanation


def test_llm_timeout_and_api_error_fallback():
    """Test that LLM network timeouts and API errors fall back cleanly to deterministic reasoning."""
    with patch.object(settings, "OPENAI_API_KEY", "sk-mock-key-12345"):
        with patch("openai.OpenAI") as mock_openai:
            mock_client = MagicMock()
            mock_openai.return_value = mock_client
            mock_client.chat.completions.create.side_effect = TimeoutError("Request timed out")

            engine = OpenAIReasoningEngine()
            context = {
                "potential_revenue": 38400.0,
                "customer_count": 23,
                "confidence": 0.94,
                "risk": "low",
                "recommended_action": "payment_recovery_link",
            }
            res = engine.generate_opportunity_reasoning("payment_recovery", context)

            assert res.reasoning_source == "deterministic"
            assert res.explanation is not None


def test_llm_cannot_bypass_guardian(db_session: Session):
    """
    CRITICAL TEST: Ensure that even if the LLM suggests an aggressive or unsafe action
    (e.g., 35% discount), the Guardian deterministically blocks it.
    """
    merchant = db_session.query(Merchant).first()
    opp = db_session.query(Opportunity).first()

    # Strategist proposes an action with 35% discount (exceeding Guardian cap of 15%)
    action = StrategistAgent.propose_action(
        db=db_session,
        opportunity=opp,
        override_discount_percent=35.0,  # Unsafe discount
    )

    # Guardian must evaluate and BLOCK the action regardless of LLM rationale
    guardian_result = GuardianAgent.evaluate_and_apply(db_session, action)

    assert guardian_result.decision == "blocked"
    assert action.status == "blocked"
    assert "exceeds maximum merchant policy" in guardian_result.reason
