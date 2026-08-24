from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, ConfigDict


class AuditEventResponse(BaseModel):
    id: str
    merchant_id: str
    action_id: Optional[str] = None
    agent: str
    event_type: str
    reason: str
    metadata_json: Dict[str, Any]
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AuditListResponse(BaseModel):
    items: List[AuditEventResponse]
    total: int
    page: int
    limit: int
