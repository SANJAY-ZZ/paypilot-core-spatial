from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from backend.app.services.opportunity_engine import opportunity_engine
from backend.app.models.opportunity import Opportunity
from backend.app.models.merchant import Merchant


def test_payment_recovery_detection(db_session: Session):
    """Test that OpportunityEngine detects unresolved failed checkout payments."""
    merchant = db_session.query(Merchant).first()
    opp = opportunity_engine.discover_payment_recovery(db_session, merchant.id)

    assert opp is not None
    assert opp.type == "payment_recovery"
    assert opp.affected_customer_count == 23
    assert opp.potential_revenue == 38400.0
    assert opp.confidence >= 0.90
    assert opp.risk == "low"
    assert "23 customers experienced payment failure" in opp.reason


def test_customer_winback_detection(db_session: Session):
    """Test that OpportunityEngine detects dormant high-value customers for win-back."""
    merchant = db_session.query(Merchant).first()
    opp = opportunity_engine.discover_customer_winback(db_session, merchant.id)

    assert opp is not None
    assert opp.type == "customer_winback"
    assert opp.affected_customer_count > 0
    assert opp.potential_revenue > 0
    assert opp.confidence >= 0.80
    assert opp.recommended_action == "winback_discount_campaign"


def test_opportunities_api_list_and_get(client: TestClient):
    """Test listing opportunities via REST API."""
    response = client.get("/api/opportunities")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 20
    assert data["total_potential_revenue"] > 0
    assert len(data["items"]) > 0

    first_item = data["items"][0]
    opp_id = first_item["id"]

    # Test single get
    detail_res = client.get(f"/api/opportunities/{opp_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["id"] == opp_id
    assert "metadata" in detail_data
    assert "suggested_payload" in detail_data
