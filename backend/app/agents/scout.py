from typing import List
from sqlalchemy.orm import Session
from backend.app.models.opportunity import Opportunity
from backend.app.services.opportunity_engine import opportunity_engine


class ScoutAgent:
    """
    SCOUT AGENT:
    Discovers raw candidate revenue opportunities across merchant's transaction and customer graph.
    Scout does not execute actions.
    """

    NAME = "scout"

    @classmethod
    def discover_opportunities(cls, db: Session, merchant_id: str) -> List[Opportunity]:
        return opportunity_engine.scan_all_opportunities(db, merchant_id)
