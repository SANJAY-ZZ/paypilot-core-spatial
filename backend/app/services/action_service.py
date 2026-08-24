from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from backend.app.models.ai_action import AIAction
from backend.app.models.opportunity import Opportunity
from backend.app.agents.scout import ScoutAgent
from backend.app.agents.analyst import AnalystAgent
from backend.app.agents.strategist import StrategistAgent
from backend.app.agents.guardian import GuardianAgent
from backend.app.agents.executor import ExecutorAgent
from backend.app.agents.auditor import AuditorAgent
from backend.app.schemas.action import (
    ActionPreviewRequest,
    ActionPreviewResponse,
    ActionApproveRequest,
    ActionExecuteRequest,
    ActionResponse,
)
from backend.app.core.errors import OpportunityNotFoundError, ActionNotFoundError, PayPilotBaseException


class ActionService:
    """Orchestrates action lifecycle across Strategist, Guardian, and Executor agents."""

    @staticmethod
    def preview_action(db: Session, request: ActionPreviewRequest) -> ActionPreviewResponse:
        opportunity = db.query(Opportunity).filter(Opportunity.id == request.opportunity_id).first()
        if not opportunity:
            raise OpportunityNotFoundError(request.opportunity_id)

        merchant_id = request.merchant_id or opportunity.merchant_id

        # 1. Analyst Agent analyzes opportunity
        AnalystAgent.analyze_opportunity(db, opportunity)

        # 2. Strategist Agent packages proposed action
        action = StrategistAgent.propose_action(
            db=db,
            opportunity=opportunity,
            override_discount_percent=request.override_discount_percent,
            override_budget=request.override_budget,
            target_customer_ids=request.target_customer_ids,
        )

        # 3. Guardian Agent applies policy checks
        guardian_result = GuardianAgent.evaluate_and_apply(db, action)

        return ActionPreviewResponse(
            action_id=action.id,
            opportunity_id=opportunity.id,
            merchant_id=merchant_id,
            agent=action.agent,
            action_type=action.action_type,
            confidence=action.confidence,
            status=action.status,
            payload=action.payload,
            guardian_result=guardian_result,
            estimated_revenue=float(action.payload.get("estimated_revenue", 0.0)),
            estimated_cost=float(action.payload.get("estimated_cost", 0.0)),
            created_at=action.created_at,
        )

    @staticmethod
    def approve_action(db: Session, request: ActionApproveRequest) -> ActionResponse:
        action = db.query(AIAction).filter(AIAction.id == request.action_id).first()
        if not action:
            raise ActionNotFoundError(request.action_id)

        if action.status == "blocked":
            raise PayPilotBaseException(
                "Cannot approve an action that was strictly BLOCKED by Guardian policy.",
                status_code=403,
                details={"guardian_result": action.guardian_result},
            )

        if action.status == "executed":
            raise PayPilotBaseException("Action has already been executed.", status_code=400)

        action.status = "approved"
        db.commit()
        db.refresh(action)

        # Record merchant approval in audit trail
        AuditorAgent.record(
            db=db,
            merchant_id=action.merchant_id,
            agent="merchant",
            action_id=action.id,
            event_type="MERCHANT_APPROVED",
            reason=request.approval_notes or "Merchant explicitly authorized action execution.",
            metadata={"notes": request.approval_notes, "status": action.status},
        )

        return ActionResponse.model_validate(action)

    @staticmethod
    def execute_action(db: Session, request: ActionExecuteRequest) -> ActionResponse:
        action = db.query(AIAction).filter(AIAction.id == request.action_id).first()
        if not action:
            raise ActionNotFoundError(request.action_id)

        # Delegate to Executor Agent
        ExecutorAgent.execute_action(
            db=db,
            action=action,
            idempotency_key=request.idempotency_key,
        )

        db.refresh(action)
        return ActionResponse.model_validate(action)

    @staticmethod
    def get_action(db: Session, action_id: str) -> ActionResponse:
        action = db.query(AIAction).filter(AIAction.id == action_id).first()
        if not action:
            raise ActionNotFoundError(action_id)
        return ActionResponse.model_validate(action)

    @staticmethod
    def list_actions(db: Session, merchant_id: str, limit: int = 50, offset: int = 0) -> tuple[List[AIAction], int]:
        query = db.query(AIAction).filter(AIAction.merchant_id == merchant_id)
        total = query.count()
        actions = query.order_by(desc(AIAction.created_at)).offset(offset).limit(limit).all()
        return actions, total


action_service = ActionService()
