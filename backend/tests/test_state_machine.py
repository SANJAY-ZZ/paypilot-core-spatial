from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.app.models.ai_action import AIAction
from backend.app.models.merchant import Merchant


def test_blocked_action_cannot_execute(client: TestClient, db_session: Session):
    """Test that an action explicitly marked 'blocked' cannot be executed."""
    merchant = db_session.query(Merchant).first()

    blocked_action = AIAction(
        id="act_blocked_test_01",
        merchant_id=merchant.id,
        agent="strategist",
        action_type="winback_discount_campaign",
        payload={"discount_percent": 30.0},  # Exceeds 15%
        confidence=0.80,
        status="blocked",
        guardian_result={"decision": "blocked", "reason": "Excessive discount"},
    )
    db_session.add(blocked_action)
    db_session.commit()

    res = client.post("/api/actions/execute", json={"action_id": blocked_action.id})
    assert res.status_code == 403
    data = res.json()
    assert "blocked" in data["message"].lower()


def test_awaiting_approval_action_cannot_execute_without_approval(client: TestClient, db_session: Session):
    """Test that an action marked 'awaiting_approval' cannot execute before merchant approval."""
    merchant = db_session.query(Merchant).first()

    approval_action = AIAction(
        id="act_awaiting_appr_01",
        merchant_id=merchant.id,
        agent="strategist",
        action_type="winback_discount_campaign",
        payload={"estimated_revenue": 10000.0, "campaign_budget": 8000.0},
        confidence=0.85,
        status="awaiting_approval",
        guardian_result={"decision": "requires_approval", "reason": "Exposure > ₹5,000"},
    )
    db_session.add(approval_action)
    db_session.commit()

    # Attempt execute directly -> should return 409 Conflict
    res = client.post("/api/actions/execute", json={"action_id": approval_action.id})
    assert res.status_code == 409
    data = res.json()
    assert "awaiting merchant approval" in data["message"].lower()

    # Now approve action
    appr_res = client.post("/api/actions/approve", json={"action_id": approval_action.id})
    assert appr_res.status_code == 200
    assert appr_res.json()["status"] == "approved"

    # Now execute -> should succeed
    exec_res = client.post("/api/actions/execute", json={"action_id": approval_action.id})
    assert exec_res.status_code == 200
    assert exec_res.json()["status"] == "executed"
