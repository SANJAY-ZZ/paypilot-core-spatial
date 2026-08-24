from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.app.models.opportunity import Opportunity
from backend.app.models.ai_action import AIAction


def test_action_preview_and_guardian_evaluation(client: TestClient, db_session: Session):
    """Test generating a proposed action preview with Guardian evaluation."""
    opp = db_session.query(Opportunity).first()
    assert opp is not None

    preview_res = client.post(
        "/api/actions/preview",
        json={"opportunity_id": opp.id},
    )
    assert preview_res.status_code == 200
    data = preview_res.json()
    assert data["action_id"] is not None
    assert data["status"] in ["approved", "awaiting_approval", "blocked"]
    assert "guardian_result" in data
    assert data["guardian_result"]["decision"] is not None


def test_execution_blocked_when_guardian_blocks(client: TestClient, db_session: Session):
    """Test that an action blocked by Guardian cannot be executed."""
    opp = db_session.query(Opportunity).first()

    # Preview with excessive discount to trigger Guardian block
    preview_res = client.post(
        "/api/actions/preview",
        json={
            "opportunity_id": opp.id,
            "override_discount_percent": 40.0,  # Violates 15% cap
        },
    )
    assert preview_res.status_code == 200
    preview_data = preview_res.json()
    assert preview_data["status"] == "blocked"

    # Attempt to execute blocked action -> should return 403 Forbidden
    exec_res = client.post(
        "/api/actions/execute",
        json={"action_id": preview_data["action_id"]},
    )
    assert exec_res.status_code == 403
    err = exec_res.json()
    assert "blocked" in err["message"].lower()


def test_approval_required_workflow_and_successful_execution(client: TestClient, db_session: Session):
    """Test action requiring approval cannot execute until approved by merchant."""
    opp = db_session.query(Opportunity).first()

    # Preview with high budget to trigger approval requirement (> ₹5,000)
    preview_res = client.post(
        "/api/actions/preview",
        json={
            "opportunity_id": opp.id,
            "override_budget": 8000.0,
            "override_discount_percent": 5.0,
        },
    )
    assert preview_res.status_code == 200
    preview_data = preview_res.json()
    action_id = preview_data["action_id"]
    assert preview_data["status"] == "awaiting_approval"

    # 1. Attempt execute before approval -> should return 409 Conflict
    exec_res1 = client.post(
        "/api/actions/execute",
        json={"action_id": action_id},
    )
    assert exec_res1.status_code == 409

    # 2. Approve action
    appr_res = client.post(
        "/api/actions/approve",
        json={"action_id": action_id, "approval_notes": "Approved by merchant admin."},
    )
    assert appr_res.status_code == 200
    appr_data = appr_res.json()
    assert appr_data["status"] == "approved"

    # 3. Execute approved action -> should succeed
    exec_res2 = client.post(
        "/api/actions/execute",
        json={"action_id": action_id},
    )
    assert exec_res2.status_code == 200
    exec_data = exec_res2.json()
    assert exec_data["status"] == "executed"
    assert exec_data["execution_result"] is not None


def test_idempotent_execution(client: TestClient, db_session: Session):
    """Test that executing twice with the same idempotency key returns the same result."""
    opp = db_session.query(Opportunity).first()

    # Preview compliant action
    preview_res = client.post(
        "/api/actions/preview",
        json={
            "opportunity_id": opp.id,
            "override_discount_percent": 0.0,
            "override_budget": 500.0,
        },
    )
    assert preview_res.status_code == 200
    action_id = preview_res.json()["action_id"]

    idempotency_key = f"idem_key_test_{action_id}"

    # First execution
    exec1 = client.post(
        "/api/actions/execute",
        json={"action_id": action_id, "idempotency_key": idempotency_key},
        headers={"X-Idempotency-Key": idempotency_key},
    )
    assert exec1.status_code == 200
    res1 = exec1.json()
    assert res1["status"] == "executed"

    # Duplicate execution with same idempotency key
    exec2 = client.post(
        "/api/actions/execute",
        json={"action_id": action_id, "idempotency_key": idempotency_key},
        headers={"X-Idempotency-Key": idempotency_key},
    )
    assert exec2.status_code == 200
    res2 = exec2.json()
    assert res2["status"] == "executed"
    assert res2["execution_result"] == res1["execution_result"]
