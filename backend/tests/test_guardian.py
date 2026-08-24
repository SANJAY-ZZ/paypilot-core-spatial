from sqlalchemy.orm import Session
from backend.app.services.guardian_service import guardian_service
from backend.app.models.merchant import Merchant


def test_guardian_approves_valid_action(db_session: Session):
    """Test Guardian approves compliant action within policy boundaries."""
    merchant = db_session.query(Merchant).first()
    payload = {
        "discount_percent": 10.0,
        "campaign_budget": 2500.0,
        "customer_count": 100,
    }
    result = guardian_service.evaluate_action(
        db=db_session,
        merchant_id=merchant.id,
        action_payload=payload,
        confidence=0.85,
        estimated_amount=2500.0,
    )

    assert result.decision == "approved"
    assert result.risk_level == "low"
    assert all(c.passed for c in result.policy_checks)


def test_guardian_blocks_excessive_discount(db_session: Session):
    """Test Guardian blocks action when discount exceeds 15%."""
    merchant = db_session.query(Merchant).first()
    payload = {
        "discount_percent": 30.0,  # Exceeds max 15.0%
        "campaign_budget": 3000.0,
        "customer_count": 50,
    }
    result = guardian_service.evaluate_action(
        db=db_session,
        merchant_id=merchant.id,
        action_payload=payload,
        confidence=0.90,
        estimated_amount=3000.0,
    )

    assert result.decision == "blocked"
    assert result.risk_level == "high"
    assert any(c.rule_name == "max_discount_percent" and not c.passed for c in result.policy_checks)
    assert "exceeds maximum merchant policy" in result.reason


def test_guardian_blocks_low_confidence(db_session: Session):
    """Test Guardian blocks action with confidence below 75%."""
    merchant = db_session.query(Merchant).first()
    payload = {
        "discount_percent": 5.0,
        "campaign_budget": 1000.0,
        "customer_count": 50,
    }
    result = guardian_service.evaluate_action(
        db=db_session,
        merchant_id=merchant.id,
        action_payload=payload,
        confidence=0.60,  # Below 0.75
        estimated_amount=1000.0,
    )

    assert result.decision == "blocked"
    assert any(c.rule_name == "min_ai_confidence" and not c.passed for c in result.policy_checks)


def test_guardian_requires_approval_above_threshold(db_session: Session):
    """Test Guardian requires explicit merchant approval when financial exposure exceeds ₹5,000."""
    merchant = db_session.query(Merchant).first()
    payload = {
        "discount_percent": 10.0,
        "campaign_budget": 8000.0,  # Exceeds approval threshold of ₹5,000 but within max budget ₹10,000
        "customer_count": 100,
    }
    result = guardian_service.evaluate_action(
        db=db_session,
        merchant_id=merchant.id,
        action_payload=payload,
        confidence=0.88,
        estimated_amount=8000.0,
    )

    assert result.decision == "requires_approval"
    assert result.risk_level == "medium"
    assert "Explicit merchant sign-off is required" in result.reason
