import math
from backend.app.schemas.simulation import (
    SimulationRequest,
    SimulationResponse,
    SimulationBreakdown,
)
from backend.app.core.config import settings


class SimulationEngine:
    """Financial calculation and outcome simulation engine for merchant campaigns."""

    @staticmethod
    def simulate(request: SimulationRequest) -> SimulationResponse:
        customers = request.customer_count
        base_conv = request.conversion_rate
        aov = request.average_order_value
        discount = request.discount_percent
        budget = request.campaign_budget
        days = request.duration_days

        # Elasticity: discount enhances conversion up to a natural saturation cap
        discount_boost = (discount / 100.0) * 0.4
        effective_conv = min(0.95, base_conv * (1.0 + discount_boost))

        # Expected orders
        expected_orders = max(1, int(round(customers * effective_conv)))

        # Gross & Net revenue
        gross_revenue = round(expected_orders * aov, 2)
        total_discount_cost = round(gross_revenue * (discount / 100.0), 2)
        net_revenue = round(gross_revenue - total_discount_cost, 2)

        # Marketing & total costs
        marketing_cost = round(budget, 2)
        total_campaign_cost = round(total_discount_cost + marketing_cost, 2)

        # Baseline margin assumption (e.g. 50% gross margin on retail items)
        gross_margin_contribution = round(gross_revenue * 0.50, 2)
        projected_net_gain = round(gross_margin_contribution - total_campaign_cost, 2)

        # If net gain is negative due to high budget/discount, reflect accurately
        roi_percentage = (
            round((projected_net_gain / total_campaign_cost) * 100.0, 2)
            if total_campaign_cost > 0
            else 0.0
        )

        cpa = round(total_campaign_cost / expected_orders, 2) if expected_orders > 0 else 0.0
        revenue_per_customer = round(net_revenue / customers, 2) if customers > 0 else 0.0

        # Confidence calculation based on statistical sample size
        # More customers & moderate duration gives higher confidence
        sample_factor = min(1.0, math.sqrt(customers) / 25.0)
        confidence = round(min(0.96, max(0.65, 0.70 + (0.25 * sample_factor))), 2)

        # Guardian Pre-Check Status
        guardian_status = "compliant"
        if discount > settings.DEFAULT_MAX_DISCOUNT_PERCENT or budget > settings.DEFAULT_MAX_CAMPAIGN_BUDGET:
            guardian_status = "violates_policy"
        elif total_campaign_cost > settings.DEFAULT_REQUIRE_APPROVAL_ABOVE_AMOUNT:
            guardian_status = "requires_guardian_override"

        # Risk level determination
        if projected_net_gain > 0 and roi_percentage > 50:
            risk_level = "low"
            rec_prefix = "High return potential."
        elif projected_net_gain > 0:
            risk_level = "medium"
            rec_prefix = "Moderate return potential."
        else:
            risk_level = "high"
            rec_prefix = "Negative return projected."

        recommendation = (
            f"{rec_prefix} Estimated {expected_orders} converted orders generating ₹{net_revenue:,.0f} net revenue "
            f"against ₹{total_campaign_cost:,.0f} in total costs (Projected ROI: {roi_percentage}%)."
        )

        breakdown = SimulationBreakdown(
            gross_revenue=gross_revenue,
            total_discount_cost=total_discount_cost,
            marketing_cost=marketing_cost,
            net_gain=projected_net_gain,
            roi_percentage=roi_percentage,
            cost_per_acquisition=cpa,
            revenue_per_targeted_customer=revenue_per_customer,
        )

        return SimulationResponse(
            expected_orders=expected_orders,
            expected_revenue=net_revenue,
            campaign_cost=total_campaign_cost,
            projected_net_gain=projected_net_gain,
            confidence=confidence,
            recommendation=recommendation,
            breakdown=breakdown,
            risk_level=risk_level,
            guardian_precheck_status=guardian_status,
        )


simulation_engine = SimulationEngine()
