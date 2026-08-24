from fastapi.testclient import TestClient
from backend.app.services.simulation_engine import simulation_engine
from backend.app.schemas.simulation import SimulationRequest


def test_simulator_calculations():
    """Test deterministic outcome simulation calculation engine."""
    # 1. Test small compliant campaign (total cost <= ₹5,000)
    small_req = SimulationRequest(
        discount_percent=5.0,
        campaign_budget=500.0,
        customer_count=40,
        average_order_value=800.0,
        conversion_rate=0.25,
        duration_days=7,
    )
    small_res = simulation_engine.simulate(small_req)
    assert small_res.expected_orders > 0
    assert small_res.expected_revenue > 0
    assert small_res.campaign_cost <= 5000.0
    assert small_res.guardian_precheck_status == "compliant"

    # 2. Test larger campaign triggering approval threshold
    large_req = SimulationRequest(
        discount_percent=10.0,
        campaign_budget=2500.0,
        customer_count=200,
        average_order_value=2200.0,
        conversion_rate=0.25,
        duration_days=14,
    )
    large_res = simulation_engine.simulate(large_req)
    assert large_res.expected_orders > 0
    assert large_res.expected_revenue > 0
    assert large_res.campaign_cost > 0
    assert large_res.confidence >= 0.70
    assert large_res.breakdown.gross_revenue >= large_res.expected_revenue
    assert large_res.guardian_precheck_status == "requires_guardian_override"


def test_simulator_api_endpoint(client: TestClient):
    """Test POST /api/simulate endpoint."""
    payload = {
        "discount_percent": 12.0,
        "campaign_budget": 3500.0,
        "customer_count": 150,
        "average_order_value": 2500.0,
        "conversion_rate": 0.20,
        "duration_days": 14,
    }
    response = client.post("/api/simulate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "expected_orders" in data
    assert "expected_revenue" in data
    assert "projected_net_gain" in data
    assert "breakdown" in data
    assert "recommendation" in data
