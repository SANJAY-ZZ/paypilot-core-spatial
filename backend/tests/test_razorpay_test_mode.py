from unittest.mock import MagicMock, patch
import pytest
import httpx
from backend.app.core.config import settings
from backend.app.core.errors import PayPilotBaseException
from backend.app.services.razorpay_service import (
    MockRazorpayService,
    RazorpayTestService,
    get_razorpay_service,
)


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


def test_razorpay_test_service_missing_credentials():
    """Test that RazorpayTestService raises clear error if credentials are missing."""
    with patch.object(settings, "RAZORPAY_KEY_ID", ""):
        with patch.object(settings, "RAZORPAY_KEY_SECRET", ""):
            with pytest.raises(PayPilotBaseException) as exc_info:
                RazorpayTestService()
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
