"""Notification and BackgroundJobLog Pydantic schemas."""

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict

NotificationType = Literal["upcoming_deadline", "overdue_task", "task_assignment"]
BackgroundJobStatus = Literal["completed", "skipped", "failed"]


class NotificationResponse(BaseModel):
    """Persistent user notification payload."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    task_id: Optional[int]
    message: str
    notification_type: NotificationType
    is_read: bool
    created_at: datetime


class NotificationListResponse(BaseModel):
    """Paginated notifications list with live unread count."""

    items: List[NotificationResponse]
    total: int
    unread_count: int
    skip: int
    limit: int


class NotificationReadAllResponse(BaseModel):
    """Result of marking all user notifications as read."""

    updated_count: int
    message: str


class BackgroundJobLogResponse(BaseModel):
    """Audit record of a FastAPI BackgroundTasks reminder run."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    job_type: str
    task_id: Optional[int]
    status: BackgroundJobStatus
    attempts: int
    result_summary: Optional[str]
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime
