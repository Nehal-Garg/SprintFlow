"""Activity log Pydantic schemas."""

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel

ActivityEntityType = Literal["project", "user_story", "task"]


class ActivityLogResponse(BaseModel):
    """Single chronological activity entry."""

    id: int
    user_id: Optional[int]
    user_name: Optional[str] = None
    project_id: Optional[int]
    project_name: Optional[str] = None
    action: str
    entity_type: ActivityEntityType
    entity_id: int
    description: str
    created_at: datetime


class ActivityLogListResponse(BaseModel):
    """Paginated list of chronological activity records."""

    items: List[ActivityLogResponse]
    total: int
    skip: int
    limit: int
