from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.core.database import get_db
from backend.app.models.opportunity import Opportunity
from backend.app.models.merchant import Merchant
from backend.app.schemas.opportunity import (
    OpportunityResponse,
    OpportunityDetailResponse,
    OpportunityListResponse,
)
from backend.app.agents.scout import ScoutAgent
from backend.app.agents.analyst import AnalystAgent
from backend.app.core.errors import OpportunityNotFoundError, PayPilotBaseException

router = APIRouter(prefix="/opportunities", tags=["Opportunities"])


@router.get("", response_model=OpportunityListResponse)
def list_opportunities(
    merchant_id: Optional[str] = Query(None, description="Filter by Merchant ID"),
    type: Optional[str] = Query(None, description="Filter by opportunity type"),
    status: Optional[str] = Query(None, description="Filter by opportunity status"),
    min_confidence: Optional[float] = Query(None, description="Filter by minimum AI confidence"),
    db: Session = Depends(get_db),
):
    """List all AI-discovered revenue opportunities with optional filtering."""
    query = db.query(Opportunity)

    if merchant_id:
        query = query.filter(Opportunity.merchant_id == merchant_id)
    else:
        # Default to first merchant if not provided
        merchant = db.query(Merchant).first()
        if merchant:
            query = query.filter(Opportunity.merchant_id == merchant.id)

    if type:
        query = query.filter(Opportunity.type == type)
    if status:
        query = query.filter(Opportunity.status == status)
    if min_confidence is not None:
        query = query.filter(Opportunity.confidence >= min_confidence)

    items = query.order_by(desc(Opportunity.potential_revenue)).all()
    total_potential = sum(item.potential_revenue for item in items)

    return OpportunityListResponse(
        items=[OpportunityResponse.model_validate(o) for o in items],
        total=len(items),
        total_potential_revenue=round(total_potential, 2),
    )


@router.get("/{opportunity_id}", response_model=OpportunityDetailResponse)
def get_opportunity(
    opportunity_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve detailed analytics and recommended action structure for a single opportunity."""
    opp = db.query(Opportunity).filter(Opportunity.id == opportunity_id).first()
    if not opp:
        raise OpportunityNotFoundError(opportunity_id)

    # Enrich with Analyst agent insights
    analysis = AnalystAgent.analyze_opportunity(db, opp)

    suggested_payload = {
        "action_type": opp.recommended_action,
        "discount_percent": 10.0 if opp.type == "customer_winback" else 0.0,
        "campaign_budget": 3500.0 if opp.type == "customer_winback" else 500.0,
        "target_customer_count": opp.affected_customer_count,
    }

    return OpportunityDetailResponse(
        id=opp.id,
        merchant_id=opp.merchant_id,
        type=opp.type,
        title=opp.title,
        potential_revenue=opp.potential_revenue,
        confidence=opp.confidence,
        risk=opp.risk,
        affected_customer_count=opp.affected_customer_count,
        reason=analysis.get("reason", opp.reason),
        reasoning=analysis.get("reasoning", opp.reason),
        reasoning_source=analysis.get("reasoning_source", "deterministic"),
        key_factors=analysis.get("key_factors", []),
        recommended_action=opp.recommended_action,
        status=opp.status,
        created_at=opp.created_at,
        metadata=analysis.get("supporting_evidence"),
        historical_recovery_rate=0.74,
        suggested_payload=suggested_payload,
    )


@router.post("/scan", response_model=List[OpportunityResponse])
def trigger_scout_scan(
    merchant_id: Optional[str] = Query(None, description="Merchant ID to scan"),
    db: Session = Depends(get_db),
):
    """Trigger the Scout agent on-demand to scan the database and detect fresh revenue opportunities."""
    if not merchant_id:
        merchant = db.query(Merchant).first()
        if not merchant:
            raise PayPilotBaseException("Merchant not found.", status_code=404)
        merchant_id = merchant.id

    discovered = ScoutAgent.discover_opportunities(db, merchant_id)
    return [OpportunityResponse.model_validate(o) for o in discovered]
