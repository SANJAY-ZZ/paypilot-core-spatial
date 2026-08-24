import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime
from backend.app.core.database import Base


class ProcessedWebhookEvent(Base):
    __tablename__ = "processed_webhook_events"

    id = Column(String(64), primary_key=True, default=lambda: f"wbev_{uuid.uuid4().hex[:12]}")
    event_id = Column(String(128), unique=True, nullable=False, index=True)
    event_type = Column(String(64), nullable=False)
    processed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
