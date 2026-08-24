from fastapi.testclient import TestClient


def test_dashboard_api(client: TestClient):
    """Test GET /api/dashboard returns coherent metrics and opportunity counts."""
    response = client.get("/api/dashboard")
    assert response.status_code == 200
    data = response.json()
    assert data["merchant_name"] == "Kora Retail"
    assert data["currency"] == "INR"
    assert data["total_revenue"] >= 800000.0
    assert data["customer_count"] == 1024
    assert data["transaction_count"] == 4892
    assert data["opportunity_count"] >= 20
    assert data["recoverable_revenue"] >= 38000.0
    assert len(data["metrics_cards"]) >= 4
    assert len(data["opportunity_breakdown"]) >= 3


def test_commerce_readiness_api(client: TestClient):
    """Test GET /api/commerce-readiness returns calculated score, categories, and recommendations."""
    response = client.get("/api/commerce-readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["merchant_name"] == "Kora Retail"
    assert data["overall_score"] >= 75
    assert data["grade"] in ["A+", "A", "B", "C"]
    assert len(data["categories"]) == 6
    assert len(data["recommendations"]) >= 3


def test_guardian_policies_api(client: TestClient):
    """Test GET and PUT /api/guardian/policies."""
    # 1. Get current policy
    res = client.get("/api/guardian/policies")
    assert res.status_code == 200
    policy = res.json()
    assert policy["max_discount_percent"] == 15.0
    assert policy["max_campaign_budget"] == 10000.0

    # 2. Update policy
    put_res = client.put(
        "/api/guardian/policies",
        json={"max_discount_percent": 18.0, "max_campaign_budget": 12000.0},
    )
    assert put_res.status_code == 200
    updated = put_res.json()
    assert updated["max_discount_percent"] == 18.0
    assert updated["max_campaign_budget"] == 12000.0


def test_customers_api(client: TestClient):
    """Test GET /api/customers listing and single customer retrieval."""
    res = client.get("/api/customers?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1024
    assert len(data["items"]) == 10

    first_cust_id = data["items"][0]["id"]
    cust_res = client.get(f"/api/customers/{first_cust_id}")
    assert cust_res.status_code == 200
    cust = cust_res.json()
    assert cust["id"] == first_cust_id
    assert "segment" in cust
