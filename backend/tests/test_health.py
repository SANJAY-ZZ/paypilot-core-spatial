from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    """Test that /health returns healthy status and system metadata."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "PayPilot AI Revenue Engine"
    assert data["razorpay_mode"] == "mock"
    assert "version" in data
