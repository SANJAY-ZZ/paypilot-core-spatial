from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.app.services.audit_service import audit_service
from backend.app.models.merchant import Merchant


def test_audit_event_creation_and_retrieval(db_session: Session, client: TestClient):
    """Test creating audit events and querying them via the REST API."""
    merchant = db_session.query(Merchant).first()

    # Record direct audit event
    event = audit_service.record_event(
        db=db_session,
        merchant_id=merchant.id,
        agent="guardian",
        event_type="TEST_POLICY_CHECK",
        reason="Automated test verification of audit trail integrity.",
        metadata={"rule": "test_rule", "passed": True},
    )
    assert event.id is not None

    # Query via REST API
    res = client.get(f"/api/audit?agent=guardian")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert any(e["event_type"] == "TEST_POLICY_CHECK" for e in data["items"])


def test_audit_filters(client: TestClient):
    """Test audit log filtering by event_type and pagination."""
    res = client.get("/api/audit?page=1&limit=10")
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) <= 10
