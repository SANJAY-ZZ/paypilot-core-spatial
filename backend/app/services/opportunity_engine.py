from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from backend.app.models.merchant import Merchant
from backend.app.models.customer import Customer
from backend.app.models.payment import Payment
from backend.app.models.order import Order
from backend.app.models.product import Product
from backend.app.models.opportunity import Opportunity
from backend.app.services.reasoning_service import reasoning_service
from backend.app.services.audit_service import audit_service


class OpportunityEngine:
    """Core analytical engine discovering and evaluating revenue opportunities."""

    @classmethod
    def discover_payment_recovery(cls, db: Session, merchant_id: str) -> Optional[Opportunity]:
        """
        Detect unresolved failed payments.
        Finds customers with failed transactions that have not yet been successfully completed.
        """
        # Find one-time failed payments (excluding subscription mandate failures)
        failed_payments = (
            db.query(Payment)
            .filter(
                Payment.merchant_id == merchant_id,
                Payment.status == "failed",
                ~Payment.failure_reason.ilike("%mandate%"),
            )
            .all()
        )

        if not failed_payments:
            return None

        # Check which customers do NOT have a successful payment created AFTER their last failure
        unresolved_by_customer: Dict[str, List[Payment]] = {}
        for p in failed_payments:
            # Check if customer has a later successful payment
            has_later_success = (
                db.query(Payment)
                .filter(
                    Payment.customer_id == p.customer_id,
                    Payment.status == "success",
                    Payment.created_at > p.created_at,
                )
                .first()
            )
            if not has_later_success:
                if p.customer_id not in unresolved_by_customer:
                    unresolved_by_customer[p.customer_id] = []
                unresolved_by_customer[p.customer_id].append(p)

        if not unresolved_by_customer:
            return None

        affected_customer_count = len(unresolved_by_customer)
        total_failed_amount = sum(
            sum(pmt.amount for pmt in pmts) for pmts in unresolved_by_customer.values()
        )
        total_failed_count = sum(len(pmts) for pmts in unresolved_by_customer.values())

        # High confidence for payment recovery because customer intent is already established
        confidence = 0.94
        risk = "low"
        title = "Automated Failed Payment Recovery"
        recommended_action = "payment_recovery_link"

        reason = reasoning_service.explain_opportunity(
            "payment_recovery",
            {
                "currency_symbol": "₹",
                "potential_revenue": total_failed_amount,
                "customer_count": affected_customer_count,
                "lookback_hours": 72,
                "recent_failures_count": total_failed_count,
            },
        )

        return Opportunity(
            merchant_id=merchant_id,
            type="payment_recovery",
            title=title,
            potential_revenue=round(total_failed_amount, 2),
            confidence=confidence,
            risk=risk,
            affected_customer_count=affected_customer_count,
            reason=reason,
            recommended_action=recommended_action,
            status="discovered",
        )

    @classmethod
    def discover_customer_winback(cls, db: Session, merchant_id: str) -> Optional[Opportunity]:
        """
        Detect lapsed high-value customers who have not ordered in a while.
        """
        # Find dormant customers with churn_risk > 0.50 and lifetime_value > 2000
        lapsed_customers = (
            db.query(Customer)
            .filter(
                Customer.merchant_id == merchant_id,
                Customer.order_count >= 1,
                Customer.churn_risk >= 0.50,
                Customer.lifetime_value >= 2000.0,
            )
            .all()
        )

        if not lapsed_customers:
            return None

        customer_count = len(lapsed_customers)
        avg_ltv = sum(c.lifetime_value for c in lapsed_customers) / customer_count
        avg_aov = sum(c.average_order_value for c in lapsed_customers) / customer_count

        # Estimate recoverable revenue (expecting ~30% win-back conversion on targeted incentive)
        estimated_orders = customer_count * 0.30
        potential_revenue = round(estimated_orders * avg_aov, 2)

        confidence = 0.82
        risk = "medium"
        title = "Dormant High-LTV Customer Win-Back"
        recommended_action = "winback_discount_campaign"

        reason = reasoning_service.explain_opportunity(
            "customer_winback",
            {
                "currency_symbol": "₹",
                "potential_revenue": potential_revenue,
                "customer_count": customer_count,
                "avg_ltv": avg_ltv,
                "dormant_days": 45,
            },
        )

        return Opportunity(
            merchant_id=merchant_id,
            type="customer_winback",
            title=title,
            potential_revenue=potential_revenue,
            confidence=confidence,
            risk=risk,
            affected_customer_count=customer_count,
            reason=reason,
            recommended_action=recommended_action,
            status="discovered",
        )

    @classmethod
    def discover_upsell(cls, db: Session, merchant_id: str) -> Optional[Opportunity]:
        """
        Detect repeat buyers with high repeat/upsell probability for targeted product cross-sell.
        """
        upsell_candidates = (
            db.query(Customer)
            .filter(
                Customer.merchant_id == merchant_id,
                Customer.order_count >= 2,
                Customer.repeat_probability >= 0.70,
            )
            .all()
        )

        if not upsell_candidates:
            return None

        customer_count = len(upsell_candidates)
        avg_aov = sum(c.average_order_value for c in upsell_candidates) / customer_count
        avg_repeat_prob = sum(c.repeat_probability for c in upsell_candidates) / customer_count

        # Upsell basket increase assumption (+35% of AOV with 40% conversion)
        potential_revenue = round(customer_count * 0.40 * (avg_aov * 0.35), 2)

        confidence = 0.88
        risk = "low"
        title = "Smart Cross-Sell for High Affinity Repeat Buyers"
        recommended_action = "smart_upsell_nudge"

        reason = reasoning_service.explain_opportunity(
            "upsell",
            {
                "currency_symbol": "₹",
                "potential_revenue": potential_revenue,
                "customer_count": customer_count,
                "avg_repeat_prob": avg_repeat_prob,
                "target_category": "Apparel & Accessories",
            },
        )

        return Opportunity(
            merchant_id=merchant_id,
            type="upsell",
            title=title,
            potential_revenue=potential_revenue,
            confidence=confidence,
            risk=risk,
            affected_customer_count=customer_count,
            reason=reason,
            recommended_action=recommended_action,
            status="discovered",
        )

    @classmethod
    def discover_subscription_recovery(cls, db: Session, merchant_id: str) -> Optional[Opportunity]:
        """
        Detect failed recurring payments / mandate failures.
        Returns None gracefully if no recurring failures exist.
        """
        recurring_failures = (
            db.query(Payment)
            .filter(
                Payment.merchant_id == merchant_id,
                Payment.status == "failed",
                Payment.failure_reason.ilike("%mandate%"),
            )
            .all()
        )

        if not recurring_failures:
            return None

        customer_count = len(set(p.customer_id for p in recurring_failures))
        total_amount = sum(p.amount for p in recurring_failures)

        confidence = 0.91
        risk = "low"
        title = "Recurring Mandate Drop-Off Recovery"
        recommended_action = "recurring_mandate_refresh"

        reason = reasoning_service.explain_opportunity(
            "subscription_recovery",
            {
                "currency_symbol": "₹",
                "potential_revenue": total_amount,
                "customer_count": customer_count,
                "failed_cycles": 1,
            },
        )

        return Opportunity(
            merchant_id=merchant_id,
            type="subscription_recovery",
            title=title,
            potential_revenue=round(total_amount, 2),
            confidence=confidence,
            risk=risk,
            affected_customer_count=customer_count,
            reason=reason,
            recommended_action=recommended_action,
            status="discovered",
        )

    @classmethod
    def scan_all_opportunities(cls, db: Session, merchant_id: str) -> List[Opportunity]:
        """
        Run full opportunity discovery across all four opportunity types.
        Saves or refreshes opportunities in the database and creates audit logs.
        """
        discovered: List[Opportunity] = []

        detectors = [
            cls.discover_payment_recovery,
            cls.discover_customer_winback,
            cls.discover_upsell,
            cls.discover_subscription_recovery,
        ]

        for detector in detectors:
            opp = detector(db, merchant_id)
            if opp:
                # Check if an opportunity of this type already exists in 'discovered' or 'analyzed' state
                existing = (
                    db.query(Opportunity)
                    .filter(
                        Opportunity.merchant_id == merchant_id,
                        Opportunity.type == opp.type,
                        Opportunity.status.in_(["discovered", "analyzed", "action_proposed"]),
                    )
                    .first()
                )

                if existing:
                    existing.title = opp.title
                    existing.potential_revenue = opp.potential_revenue
                    existing.confidence = opp.confidence
                    existing.risk = opp.risk
                    existing.affected_customer_count = opp.affected_customer_count
                    existing.reason = opp.reason
                    existing.recommended_action = opp.recommended_action
                    db.commit()
                    db.refresh(existing)
                    discovered.append(existing)
                else:
                    db.add(opp)
                    db.commit()
                    db.refresh(opp)
                    discovered.append(opp)

                    # Audit discovery event
                    audit_service.record_event(
                        db=db,
                        merchant_id=merchant_id,
                        agent="scout",
                        event_type="OPPORTUNITY_DISCOVERED",
                        reason=f"Scout agent detected {opp.type} opportunity: {opp.title}",
                        metadata={
                            "opportunity_id": opp.id,
                            "type": opp.type,
                            "potential_revenue": opp.potential_revenue,
                            "affected_customers": opp.affected_customer_count,
                        },
                    )

        return discovered


opportunity_engine = OpportunityEngine()
