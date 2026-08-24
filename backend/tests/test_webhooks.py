import hmac
import hashlib
import json
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.models.payment import Payment
from backend.app.models.ai_action import AIAction
from backend.app.models.audit_event import AuditEvent
from backend.app.models.merchant import Merchant


def generate_webhook_signature(payload_bytes: bytes, secret: str = "test_webhook_secret_paypilot") -> str:
    """Helper to compute valid Razorpay webhook signature."""
    return hmac.new(
        secret.encode("utf-8"),
        payload_bytes,
        hashlib.sha256,
    ).hexdigest()


def test_webhook_invalid_signature_rejected(client: TestClient):
    """Test that webhooks with forged/invalid signatures are rejected with HTTP 400."""
    payload = json.dumps({"event": "payment_link.paid", "event_id": "evt_fake_001"}).encode("utf-8")
    invalid_signature = "invalid_sha256_signature_hex"

    res = client.post(
        "/api/webhooks/razorpay",
        content=payload,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": invalid_signature,
        },
    )
    assert res.status_code == 400
    data = res.json()
    assert "Invalid Razorpay webhook signature" in data["message"]


def test_webhook_payment_link_paid_success(client: TestClient, db_session: Session):
    """Test payment_link.paid event updates Payment status and logs EXECUTION_SUCCESS."""
    merchant = db_session.query(Merchant).first()

    # Create a payment record to match
    test_payment = Payment(
        id="pay_webhook_test_01",
        merchant_id=merchant.id,
        customer_id="cust_kora_0001",
        amount=2500.0,
        status="failed",
        razorpay_reference="pay_rzp_mock_111",
    )
    db_session.add(test_payment)

    # Create an action record to match
    test_action = AIAction(
        id="act_webhook_test_01",
        merchant_id=merchant.id,
        agent="executor",
        action_type="payment_recovery_link",
        payload={"estimated_revenue": 2500.0},
        confidence=0.94,
        status="executing",
        idempotency_key="plink_ref_rec_111",
        execution_result={"payment_link_id": "plink_webhook_111"},
    )
    db_session.add(test_action)
    db_session.commit()

    webhook_payload = {
        "event": "payment_link.paid",
        "event_id": "evt_rzp_plink_paid_001",
        "payload": {
            "payment_link": {
                "entity": {
                    "id": "plink_webhook_111",
                    "reference_id": "plink_ref_rec_111",
                    "amount": 250000,
                    "status": "paid",
                }
            },
            "payment": {
                "entity": {
                    "id": "pay_rzp_mock_111",
                    "amount": 250000,
                    "status": "captured",
                }
            },
        },
    }
    payload_bytes = json.dumps(webhook_payload).encode("utf-8")
    valid_signature = generate_webhook_signature(payload_bytes, settings.RAZORPAY_WEBHOOK_SECRET)

    res = client.post(
        "/api/webhooks/razorpay",
        content=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": valid_signature,
        },
    )
    assert res.status_code == 200
    res_data = res.json()
    assert res_data["status"] == "success"

    # Verify Payment was marked success
    db_session.refresh(test_payment)
    assert test_payment.status == "success"

    # Verify Action was marked executed
    db_session.refresh(test_action)
    assert test_action.status == "executed"

    # Verify EXECUTION_SUCCESS audit event created
    audit = (
        db_session.query(AuditEvent)
        .filter(AuditEvent.event_type == "EXECUTION_SUCCESS", AuditEvent.action_id == test_action.id)
        .first()
    )
    assert audit is not None
    assert "paid successfully" in audit.reason


def test_webhook_idempotency_duplicate_event_handling(client: TestClient, db_session: Session):
    """Test that duplicate webhook deliveries with the same event_id are safely ignored."""
    webhook_payload = {
        "event": "payment_link.paid",
        "event_id": "evt_rzp_duplicate_check_999",
        "payload": {
            "payment_link": {
                "entity": {
                    "id": "plink_dupe_999",
                    "reference_id": "ref_dupe_999",
                    "amount": 100000,
                }
            },
            "payment": {
                "entity": {
                    "id": "pay_dupe_999",
                    "amount": 100000,
                }
            },
        },
    }
    payload_bytes = json.dumps(webhook_payload).encode("utf-8")
    sig = generate_webhook_signature(payload_bytes, settings.RAZORPAY_WEBHOOK_SECRET)

    headers = {
        "Content-Type": "application/json",
        "X-Razorpay-Signature": sig,
    }

    # First delivery
    res1 = client.post("/api/webhooks/razorpay", content=payload_bytes, headers=headers)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["status"] == "success"
    assert "idempotent" not in data1

    # Second delivery (Duplicate event)
    res2 = client.post("/api/webhooks/razorpay", content=payload_bytes, headers=headers)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["status"] == "success"
    assert data2.get("idempotent") is True


def test_webhook_unsupported_event_graceful_acknowledgement(client: TestClient):
    """Test that unsupported or informational webhook events return 200 OK without errors."""
    webhook_payload = {
        "event": "order.paid",
        "event_id": "evt_rzp_unsupported_001",
        "payload": {"order": {"entity": {"id": "order_xyz"}}},
    }
    payload_bytes = json.dumps(webhook_payload).encode("utf-8")
    sig = generate_webhook_signature(payload_bytes, settings.RAZORPAY_WEBHOOK_SECRET)

    res = client.post(
        "/api/webhooks/razorpay",
        content=payload_bytes,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert data.get("unhandled") is True
