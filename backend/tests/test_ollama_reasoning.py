import json
from unittest.mock import MagicMock, patch
import httpx
import pytest
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.services.ollama_service import (
    OllamaService,
    extract_json_from_text,
    LLMReasoningOutput,
)
from backend.app.services.reasoning_service import (
    OllamaReasoningEngine,
    DeterministicReasoningEngine,
    get_reasoning_engine,
)
from backend.app.models.merchant import Merchant
from backend.app.models.opportunity import Opportunity
from backend.app.agents.analyst import AnalystAgent
from backend.app.agents.strategist import StrategistAgent
from backend.app.agents.guardian import GuardianAgent


def test_extract_json_from_text_clean():
    """Test extracting clean direct JSON."""
    raw = '{"summary": "Test summary", "confidence": 0.9, "recommended_action": "payment_recovery_link", "key_factors": ["f1"]}'
    res = extract_json_from_text(raw)
    assert res is not None
    assert res["summary"] == "Test summary"
    assert res["confidence"] == 0.9


def test_extract_json_from_text_markdown_fences():
    """Test extracting JSON wrapped in markdown code fences."""
    raw = """Here is the analytical result:
```json
{
  "summary": "23 payments failed due to network glitch",
  "key_factors": ["High LTV customers", "72h window"],
  "recommended_action": "payment_recovery_link",
  "confidence": 0.95,
  "risk": "low"
}
```
Hope this helps!"""
    res = extract_json_from_text(raw)
    assert res is not None
    assert res["summary"] == "23 payments failed due to network glitch"
    assert res["confidence"] == 0.95


def test_extract_json_from_text_embedded():
    """Test extracting JSON embedded in text without code fences."""
    raw = 'Some preliminary thoughts... {"summary": "Embedded summary", "confidence": 0.88, "recommended_action": "winback_discount_campaign", "key_factors": []} and trailing comments.'
    res = extract_json_from_text(raw)
    assert res is not None
    assert res["summary"] == "Embedded summary"


def test_ollama_successful_reasoning():
    """Test successful Ollama reasoning generation with structured output."""
    mock_ollama_response = {
        "response": json.dumps({
            "summary": "23 customer payments failed within 72 hours with high established customer LTV, making immediate recovery highly probable.",
            "key_factors": [
                "23 payment drop-offs within 72 hours",
                "₹38,400 immediate recoverable liquidity",
                "High prior buyer affinity",
            ],
            "recommended_action": "payment_recovery_link",
            "confidence": 0.94,
            "risk": "low",
            "expected_recovery": 38400.0,
        })
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_ollama_response

    with patch("httpx.Client.post", return_value=mock_resp):
        service = OllamaService(base_url="http://localhost:11434", model="gemma4:latest")
        engine = OllamaReasoningEngine(service=service)

        context = {
            "potential_revenue": 38400.0,
            "customer_count": 23,
            "confidence": 0.94,
            "risk": "low",
            "recommended_action": "payment_recovery_link",
        }
        res = engine.generate_opportunity_reasoning("payment_recovery", context)

        assert res.reasoning_source == "ollama"
        assert "23 customer payments failed" in res.explanation
        assert len(res.key_factors) == 3
        assert res.confidence == 0.94
        assert res.risk == "low"


def test_ollama_invalid_json_fallback():
    """Test that malformed/invalid JSON from Ollama triggers deterministic fallback cleanly."""
    mock_ollama_response = {
        "response": "Sorry, I cannot provide JSON right now. Error 500."
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_ollama_response

    with patch("httpx.Client.post", return_value=mock_resp):
        service = OllamaService(base_url="http://localhost:11434", model="gemma4:latest")
        engine = OllamaReasoningEngine(service=service)

        context = {
            "potential_revenue": 38400.0,
            "customer_count": 23,
            "confidence": 0.94,
            "risk": "low",
            "recommended_action": "payment_recovery_link",
        }
        res = engine.generate_opportunity_reasoning("payment_recovery", context)

        assert res.reasoning_source == "deterministic_fallback"
        assert "23 customers experienced payment failure" in res.explanation
        assert len(res.key_factors) > 0


def test_ollama_timeout_fallback():
    """Test that HTTP timeout during Ollama generation falls back gracefully."""
    with patch("httpx.Client.post", side_effect=httpx.TimeoutException("Timeout after 120s")):
        service = OllamaService(base_url="http://localhost:11434", model="gemma4:latest")
        engine = OllamaReasoningEngine(service=service)

        context = {
            "potential_revenue": 38400.0,
            "customer_count": 23,
            "confidence": 0.94,
            "risk": "low",
            "recommended_action": "payment_recovery_link",
        }
        res = engine.generate_opportunity_reasoning("payment_recovery", context)

        assert res.reasoning_source == "deterministic_fallback"
        assert res.explanation is not None


def test_ollama_unavailable_fallback():
    """Test that connection error (Ollama daemon offline) falls back gracefully."""
    with patch("httpx.Client.post", side_effect=httpx.ConnectError("Connection refused on port 11434")):
        service = OllamaService(base_url="http://localhost:11434", model="gemma4:latest")
        engine = OllamaReasoningEngine(service=service)

        context = {
            "potential_revenue": 38400.0,
            "customer_count": 23,
            "confidence": 0.94,
            "risk": "low",
            "recommended_action": "payment_recovery_link",
        }
        res = engine.generate_opportunity_reasoning("payment_recovery", context)

        assert res.reasoning_source == "deterministic_fallback"
        assert res.confidence == 0.94


def test_ollama_health_check_connected():
    """Test OllamaService health probe when daemon is reachable and model is present."""
    mock_tags = {
        "models": [
            {"name": "gemma4:latest", "model": "gemma4:latest"},
            {"name": "qwen3.6:27b", "model": "qwen3.6:27b"},
        ]
    }
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_tags

    with patch("httpx.Client.get", return_value=mock_resp):
        service = OllamaService(base_url="http://localhost:11434", model="gemma4:latest")
        health = service.health_check()

        assert health["status"] == "connected"
        assert health["model"] == "gemma4:latest"
        assert health["model_available"] is True
        assert "gemma4:latest" in health["available_models"]


def test_ollama_health_check_offline():
    """Test OllamaService health probe when daemon is offline."""
    with patch("httpx.Client.get", side_effect=httpx.ConnectError("Offline")):
        service = OllamaService(base_url="http://localhost:11434", model="gemma4:latest")
        health = service.health_check()

        assert health["status"] == "unavailable"
        assert health["model_available"] is False


def test_guardian_blocks_unsafe_llm_recommendation(db_session: Session):
    """
    CRITICAL: Verify Guardian deterministically blocks an excessive discount
    recommended by the LLM (e.g. 30% discount when policy max is 15%).
    """
    merchant = db_session.query(Merchant).first()
    opp = db_session.query(Opportunity).first()

    # Strategist proposes an action with 30% discount (simulating an aggressive LLM output)
    action = StrategistAgent.propose_action(
        db=db_session,
        opportunity=opp,
        override_discount_percent=30.0,
    )

    # Guardian must deterministically evaluate and block
    guardian_result = GuardianAgent.evaluate_and_apply(db_session, action)

    assert guardian_result.decision == "blocked"
    assert action.status == "blocked"
    assert "exceeds maximum merchant policy" in guardian_result.reason


def test_guardian_approves_safe_llm_recommendation(db_session: Session):
    """
    Verify Guardian approves a safe recommendation compliant with policy.
    """
    merchant = db_session.query(Merchant).first()
    opp = db_session.query(Opportunity).first()

    action = StrategistAgent.propose_action(
        db=db_session,
        opportunity=opp,
        override_discount_percent=10.0,  # Within 15% limit
    )

    guardian_result = GuardianAgent.evaluate_and_apply(db_session, action)

    assert guardian_result.decision in ["approved", "requires_approval"]
    assert action.status in ["approved", "awaiting_approval"]
