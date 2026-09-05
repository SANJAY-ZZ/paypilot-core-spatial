from unittest.mock import MagicMock, patch
from decimal import Decimal
import pytest
import httpx
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.errors import PayPilotBaseException, GuardianBlockedError, ApprovalRequiredError
from backend.app.services.razorpay_service import (
    to_subunit,
    MockRazorpayService,
    RazorpayTestService,
    get_razorpay_service,
)
from backend.app.models.merchant import Merchant
from backend.app.models.opportunity import Opportunity
from backend.app.models.ai_action import AIAction
from backend.app.agents.strategist import StrategistAgent
from backend.app.agents.guardian import GuardianAgent
from backend.app.agents.executor import ExecutorAgent
from backend.app.services.action_service import action_service
from backend.app.schemas.action import ActionExecuteRequest


def test_to_subunit_conversion():
    """Test precise Decimal conversion from currency amount to paise."""
    assert to_subunit(100.0) == 10000
    assert to_subunit(100.50) == 10050
    assert to_subunit(0.99) == 99
    assert to_subunit("2499.00") == 249900
    assert to_subunit(Decimal("1500.75")) == 150075


def test_mock_razorpay_service_link_creation():
    """Test MockRazorpayService generates deterministic mock payment link structures."""
    svc = MockRazorpayService()
    res = svc.create_payment_link(
        amount=2499.0,
        currency="INR",
        customer_name="Aarav Sharma",
        customer_email="aarav@example.com",
        description="Recovery Link for Order 123",
        reference_id="paypilot_mock_REC_999",
    )
    assert res["id"].startswith("plink_mock_")
    assert res["amount"] == 249900  # 2499 * 100 paise
    assert res["currency"] == "INR"
    assert res["provider"] == "mock_razorpay"
    assert res["mock"] is True
    assert "https://rzp.io/i/" in res["short_url"]


def test_mock_razorpay_fetch_and_cancel():
    """Test Mock Razorpay fetch and cancel payment links."""
    svc = MockRazorpayService()
    fetched = svc.fetch_payment_link("plink_mock_12345")
    assert fetched["id"] == "plink_mock_12345"
    assert fetched["status"] == "created"

    cancelled = svc.cancel_payment_link("plink_mock_12345")
    assert cancelled["id"] == "plink_mock_12345"
    assert cancelled["status"] == "cancelled"


def test_razorpay_test_service_missing_credentials():
    """Test that RazorpayTestService raises clear error if credentials are missing."""
    with patch.object(settings, "RAZORPAY_KEY_ID", ""):
        with patch.object(settings, "RAZORPAY_KEY_SECRET", ""):
            with pytest.raises(PayPilotBaseException) as exc_info:
                RazorpayTestService(key_id="", key_secret="")
            assert "RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET must be configured" in str(exc_info.value)


def test_razorpay_test_service_creates_payment_link_with_mocked_http():
    """Test RazorpayTestService with mocked HTTP client converting INR to paise correctly."""
    mock_http_client = MagicMock(spec=httpx.Client)

    # Mock response from Razorpay Test API
    fake_response = MagicMock(spec=httpx.Response)
    fake_response.status_code = 200
    fake_response.json.return_value = {
        "id": "plink_test_8819284",
        "status": "created",
        "amount": 185000,  # 1850.00 INR in paise
        "amount_paid": 0,
        "currency": "INR",
        "description": "PayPilot AI Recovery Link",
        "reference_id": "paypilot_test_REC_881",
        "short_url": "https://rzp.io/i/plink_test_8819284",
        "customer": {"name": "Priya Patel", "email": "priya@example.com"},
        "expire_by": 1756000000,
        "created_at": 1755000000,
    }
    mock_http_client.post.return_value = fake_response

    svc = RazorpayTestService(
        key_id="rzp_test_mockKey123",
        key_secret="mockSecret456",
        http_client=mock_http_client,
    )

    result = svc.create_payment_link(
        amount=1850.0,
        currency="INR",
        customer_name="Priya Patel",
        customer_email="priya@example.com",
        description="PayPilot AI Recovery Link",
        reference_id="paypilot_test_REC_881",
    )

    assert result["id"] == "plink_test_8819284"
    assert result["amount"] == 185000
    assert result["currency"] == "INR"
    assert result["provider"] == "razorpay_test"
    assert result["mock"] is False

    # Verify HTTP POST payload structure
    mock_http_client.post.assert_called_once()
    called_url, called_kwargs = mock_http_client.post.call_args
    assert "https://api.razorpay.com/v1/payment_links" in called_url[0]
    payload = called_kwargs["json"]
    assert payload["amount"] == 185000
    assert payload["currency"] == "INR"
    assert payload["customer"]["email"] == "priya@example.com"


def test_razorpay_test_service_api_error():
    """Test Razorpay Test API returning error status code."""
    mock_http_client = MagicMock(spec=httpx.Client)
    fake_response = MagicMock(spec=httpx.Response)
    fake_response.status_code = 400
    fake_response.text = '{"error": {"description": "Invalid customer details"}}'
    mock_http_client.post.return_value = fake_response

    svc = RazorpayTestService(
        key_id="rzp_test_mockKey123",
        key_secret="mockSecret456",
        http_client=mock_http_client,
    )

    with pytest.raises(PayPilotBaseException) as exc_info:
        svc.create_payment_link(
            amount=500.0,
            currency="INR",
            customer_name="",
            customer_email="",
            description="Test fail",
        )
    assert "Razorpay Payment Link creation failed" in str(exc_info.value)


def test_razorpay_test_service_timeout():
    """Test Razorpay Test API request timeout handling."""
    mock_http_client = MagicMock(spec=httpx.Client)
    mock_http_client.post.side_effect = httpx.TimeoutException("Connection timed out")

    svc = RazorpayTestService(
        key_id="rzp_test_mockKey123",
        key_secret="mockSecret456",
        http_client=mock_http_client,
    )

    with pytest.raises(PayPilotBaseException) as exc_info:
        svc.create_payment_link(
            amount=500.0,
            currency="INR",
            customer_name="Test",
            customer_email="test@example.com",
            description="Timeout test",
        )
    assert "Razorpay Test API timed out" in str(exc_info.value)


def test_razorpay_test_service_health_check_connected():
    """Test Razorpay health check when API responds 200."""
    mock_http_client = MagicMock(spec=httpx.Client)
    fake_response = MagicMock(spec=httpx.Response)
    fake_response.status_code = 200
    fake_response.json.return_value = {"payment_links": []}
    mock_http_client.get.return_value = fake_response

    svc = RazorpayTestService(
        key_id="rzp_test_1234567890",
        key_secret="secret123",
        http_client=mock_http_client,
    )

    health = svc.health_check()
    assert health["provider"] == "razorpay"
    assert health["mode"] == "test"
    assert health["status"] == "connected"
    assert health["key_configured"] is True


def test_razorpay_test_service_health_check_invalid_credentials():
    """Test Razorpay health check when API responds 401 Unauthorized."""
    mock_http_client = MagicMock(spec=httpx.Client)
    fake_response = MagicMock(spec=httpx.Response)
    fake_response.status_code = 401
    mock_http_client.get.return_value = fake_response

    svc = RazorpayTestService(
        key_id="rzp_test_invalid",
        key_secret="wrongSecret",
        http_client=mock_http_client,
    )

    health = svc.health_check()
    assert health["status"] == "invalid_credentials"


def test_executor_idempotency_prevents_duplicate_razorpay_links(db_session: Session):
    """
    Test that executing an already-executed action returns the existing payment link
    without re-calling Razorpay.
    """
    merchant = db_session.query(Merchant).first()
    opp = db_session.query(Opportunity).first()

    action = StrategistAgent.propose_action(
        db=db_session,
        opportunity=opp,
        override_discount_percent=5.0,
    )
    GuardianAgent.evaluate_and_apply(db_session, action)
    action.status = "approved"
    db_session.commit()

    # First execution creates payment link
    first_res = ExecutorAgent.execute_action(db_session, action, idempotency_key="key_12345")
    assert first_res["status"] == "executed"
    payment_link_id = first_res["execution_result"]["payment_link_id"]
    assert payment_link_id is not None

    # Second execution returns cached result without creating a new link
    second_res = ExecutorAgent.execute_action(db_session, action, idempotency_key="key_12345")
    assert second_res.get("idempotent_replay") is True
    assert second_res["execution_result"]["payment_link_id"] == payment_link_id
