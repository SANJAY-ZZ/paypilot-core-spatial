from contextlib import asynccontextmanager
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from backend.app.core.config import settings
from backend.app.core.database import init_db, SessionLocal, engine
from backend.app.core.errors import register_error_handlers
from backend.app.core.logging import setup_logging
from backend.app.api import api_router
from backend.app.data.seed import seed_database
import logging

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle management."""
    logger.info("Initializing PayPilot database schema...")
    init_db()

    # Auto-seed if database is empty
    db = SessionLocal()
    try:
        from backend.app.models.merchant import Merchant

        has_merchant = db.query(Merchant).first()
        if not has_merchant:
            logger.info("Database empty: Running deterministic Kora Retail seed...")
            seed_database(db)
        else:
            logger.info("Database already initialized with merchant data.")
    except Exception as e:
        logger.warning(f"Auto-seed check encountered: {e}")
    finally:
        db.close()

    yield
    logger.info("PayPilot backend shutting down.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="PayPilot: AI Revenue Operating System for Merchants (Razorpay Buildathon)",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Register CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Domain Exception Handlers
register_error_handlers(app)

# Include API Router
app.include_router(api_router, prefix=settings.API_PREFIX)


from backend.app.services.ollama_service import ollama_service
from backend.app.services.razorpay_service import get_razorpay_service


@app.get("/health", tags=["Health"], status_code=status.HTTP_200_OK)
def health_check():
    """System health, database connectivity, LLM, and Razorpay telemetry probe."""
    db_healthy = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_healthy = True
    except Exception as e:
        logger.error(f"Health check DB probe error: {e}")

    llm_telemetry = {
        "provider": settings.LLM_PROVIDER,
        "model": settings.OLLAMA_MODEL if settings.LLM_PROVIDER == "ollama" else settings.LLM_MODEL,
        "status": "unavailable",
        "fallback_mode_active": True,
    }

    if settings.LLM_PROVIDER == "ollama":
        ollama_status = ollama_service.health_check()
        llm_telemetry["status"] = ollama_status.get("status", "unavailable")
        llm_telemetry["model_available"] = ollama_status.get("model_available", False)
        llm_telemetry["available_models"] = ollama_status.get("available_models", [])
        llm_telemetry["fallback_mode_active"] = ollama_status.get("status") != "connected"
    elif settings.LLM_PROVIDER == "openai":
        llm_telemetry["status"] = "configured" if settings.OPENAI_API_KEY else "unconfigured"
        llm_telemetry["fallback_mode_active"] = not bool(settings.OPENAI_API_KEY)
    else:
        llm_telemetry["status"] = "deterministic_active"
        llm_telemetry["fallback_mode_active"] = False

    razorpay_service = get_razorpay_service()
    razorpay_telemetry = razorpay_service.health_check()

    return {
        "status": "healthy" if db_healthy else "degraded",
        "service": "PayPilot AI Revenue Engine",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "database_connected": db_healthy,
        "razorpay_mode": settings.RAZORPAY_MODE,
        "razorpay": razorpay_telemetry,
        "llm": llm_telemetry,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
