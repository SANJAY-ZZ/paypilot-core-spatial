from fastapi import APIRouter
from backend.app.api.dashboard import router as dashboard_router
from backend.app.api.opportunities import router as opportunities_router
from backend.app.api.customers import router as customers_router
from backend.app.api.simulator import router as simulator_router
from backend.app.api.guardian import router as guardian_router
from backend.app.api.actions import router as actions_router
from backend.app.api.audit import router as audit_router
from backend.app.api.commerce import router as commerce_router
from backend.app.api.webhooks import router as webhooks_router

api_router = APIRouter()

api_router.include_router(dashboard_router)
api_router.include_router(opportunities_router)
api_router.include_router(customers_router)
api_router.include_router(simulator_router)
api_router.include_router(guardian_router)
api_router.include_router(actions_router)
api_router.include_router(audit_router)
api_router.include_router(commerce_router)
api_router.include_router(webhooks_router)

__all__ = ["api_router"]
