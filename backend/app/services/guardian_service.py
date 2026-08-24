from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.app.models.guardian_policy import GuardianPolicy
from backend.app.models.merchant import Merchant
from backend.app.schemas.guardian import GuardianEvaluationResult, PolicyCheckDetail
from backend.app.services.reasoning_service import reasoning_service
from backend.app.core.config import settings


class GuardianService:
    """Deterministic Guardian Policy Engine enforcing financial guardrails."""

    @staticmethod
    def get_or_create_policy(db: Session, merchant_id: str) -> GuardianPolicy:
        """Fetch active policy for merchant, or create default if none exists."""
        policy = db.query(GuardianPolicy).filter(GuardianPolicy.merchant_id == merchant_id).first()
        if not policy:
            policy = GuardianPolicy(
                merchant_id=merchant_id,
                max_discount_percent=settings.DEFAULT_MAX_DISCOUNT_PERCENT,
                max_campaign_budget=settings.DEFAULT_MAX_CAMPAIGN_BUDGET,
                max_customer_count=settings.DEFAULT_MAX_CUSTOMER_COUNT,
                min_ai_confidence=settings.DEFAULT_MIN_AI_CONFIDENCE,
                require_approval_above_amount=settings.DEFAULT_REQUIRE_APPROVAL_ABOVE_AMOUNT,
            )
            db.add(policy)
            db.commit()
            db.refresh(policy)
        return policy

    @classmethod
    def evaluate_action(
        cls,
        db: Session,
        merchant_id: str,
        action_payload: Dict[str, Any],
        confidence: float,
        estimated_amount: float,
    ) -> GuardianEvaluationResult:
        """
        Evaluate a proposed action against merchant's deterministic Guardian policy.

        Returns GuardianEvaluationResult with decision: 'approved', 'blocked', or 'requires_approval'.
        """
        policy = cls.get_or_create_policy(db, merchant_id)

        discount_percent = float(action_payload.get("discount_percent", 0.0))
        campaign_budget = float(action_payload.get("campaign_budget", action_payload.get("budget", 0.0)))
        customer_count = int(action_payload.get("customer_count", len(action_payload.get("target_customer_ids", [])) or 1))

        checks: List[PolicyCheckDetail] = []
        violations: List[str] = []
        requires_approval_reasons: List[str] = []

        # 1. Check Max Discount
        if discount_percent > policy.max_discount_percent:
            violations.append(
                f"Requested discount ({discount_percent:.1f}%) exceeds maximum merchant policy of {policy.max_discount_percent:.1f}%"
            )
            checks.append(
                PolicyCheckDetail(
                    rule_name="max_discount_percent",
                    passed=False,
                    threshold=policy.max_discount_percent,
                    actual_value=discount_percent,
                    message=f"Discount {discount_percent:.1f}% exceeds limit {policy.max_discount_percent:.1f}%",
                )
            )
        else:
            checks.append(
                PolicyCheckDetail(
                    rule_name="max_discount_percent",
                    passed=True,
                    threshold=policy.max_discount_percent,
                    actual_value=discount_percent,
                    message="Discount within allowable limit.",
                )
            )

        # 2. Check Campaign Budget
        if campaign_budget > policy.max_campaign_budget:
            violations.append(
                f"Campaign budget (₹{campaign_budget:,.0f}) exceeds merchant cap of ₹{policy.max_campaign_budget:,.0f}"
            )
            checks.append(
                PolicyCheckDetail(
                    rule_name="max_campaign_budget",
                    passed=False,
                    threshold=policy.max_campaign_budget,
                    actual_value=campaign_budget,
                    message=f"Budget ₹{campaign_budget:,.0f} exceeds max ₹{policy.max_campaign_budget:,.0f}",
                )
            )
        else:
            checks.append(
                PolicyCheckDetail(
                    rule_name="max_campaign_budget",
                    passed=True,
                    threshold=policy.max_campaign_budget,
                    actual_value=campaign_budget,
                    message="Campaign budget within allowable limit.",
                )
            )

        # 3. Check Customer Count
        if customer_count > policy.max_customer_count:
            violations.append(
                f"Target cohort size ({customer_count} customers) exceeds maximum allowable limit of {policy.max_customer_count}"
            )
            checks.append(
                PolicyCheckDetail(
                    rule_name="max_customer_count",
                    passed=False,
                    threshold=policy.max_customer_count,
                    actual_value=customer_count,
                    message=f"Target count {customer_count} exceeds limit {policy.max_customer_count}",
                )
            )
        else:
            checks.append(
                PolicyCheckDetail(
                    rule_name="max_customer_count",
                    passed=True,
                    threshold=policy.max_customer_count,
                    actual_value=customer_count,
                    message="Target customer cohort within safe limit.",
                )
            )

        # 4. Check AI Confidence
        # Convert confidence to 0.0-1.0 if passed as percentage > 1
        normalized_confidence = confidence / 100.0 if confidence > 1.0 else confidence
        if normalized_confidence < policy.min_ai_confidence:
            violations.append(
                f"AI confidence ({normalized_confidence * 100:.1f}%) is below minimum required threshold of {policy.min_ai_confidence * 100:.1f}%"
            )
            checks.append(
                PolicyCheckDetail(
                    rule_name="min_ai_confidence",
                    passed=False,
                    threshold=policy.min_ai_confidence,
                    actual_value=normalized_confidence,
                    message=f"Confidence {normalized_confidence * 100:.1f}% is lower than threshold {policy.min_ai_confidence * 100:.1f}%",
                )
            )
        else:
            checks.append(
                PolicyCheckDetail(
                    rule_name="min_ai_confidence",
                    passed=True,
                    threshold=policy.min_ai_confidence,
                    actual_value=normalized_confidence,
                    message="AI confidence satisfies safety bar.",
                )
            )

        # 5. Check Autonomous Approval Threshold (Estimated financial impact / budget)
        impact_value = max(estimated_amount, campaign_budget)
        if impact_value > policy.require_approval_above_amount:
            requires_approval_reasons.append(
                f"Estimated financial exposure (₹{impact_value:,.0f}) exceeds autonomous execution limit of ₹{policy.require_approval_above_amount:,.0f}"
            )
            checks.append(
                PolicyCheckDetail(
                    rule_name="require_approval_above_amount",
                    passed=True,  # Doesn't block, but triggers approval requirement
                    threshold=policy.require_approval_above_amount,
                    actual_value=impact_value,
                    message=f"Exposure ₹{impact_value:,.0f} requires merchant approval (> ₹{policy.require_approval_above_amount:,.0f})",
                )
            )
        else:
            checks.append(
                PolicyCheckDetail(
                    rule_name="require_approval_above_amount",
                    passed=True,
                    threshold=policy.require_approval_above_amount,
                    actual_value=impact_value,
                    message="Within autonomous financial execution threshold.",
                )
            )

        # Determine Final Decision
        if violations:
            decision = "blocked"
            risk_level = "high"
            reason = reasoning_service.explain_guardian_decision("blocked", violations, {})
        elif requires_approval_reasons:
            decision = "requires_approval"
            risk_level = "medium"
            reason = reasoning_service.explain_guardian_decision(
                "requires_approval",
                [],
                {
                    "estimated_amount": impact_value,
                    "approval_threshold": policy.require_approval_above_amount,
                },
            )
        else:
            decision = "approved"
            risk_level = "low"
            reason = reasoning_service.explain_guardian_decision("approved", [], {})

        return GuardianEvaluationResult(
            decision=decision,
            reason=reason,
            risk_level=risk_level,
            policy_checks=checks,
            metadata={
                "merchant_id": merchant_id,
                "policy_id": policy.id,
                "violations_count": len(violations),
                "requires_approval": decision == "requires_approval",
            },
        )


guardian_service = GuardianService()
