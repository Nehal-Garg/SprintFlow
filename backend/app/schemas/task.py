"""Task Pydantic schemas."""

from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

TaskPriority = Literal["Low", "Medium", "High", "Critical"]
TaskStatus = Literal["To Do", "In Progress", "In Review", "Done"]


class TaskCreateRequest(BaseModel):
    """Payload for creating a task under an existing user story."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(default=None, max_length=4000)
    assignee_id: Optional[int] = Field(default=None, ge=1)
    priority: TaskPriority = "Medium"
    status: TaskStatus = "To Do"
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    estimated_hours: Optional[float] = Field(default=None, ge=0.0, le=1000.0)
    actual_hours: Optional[float] = Field(default=None, ge=0.0, le=1000.0)

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise ValueError("Task title must contain at least 2 non-whitespace characters.")
        return cleaned

    @model_validator(mode="after")
    def validate_dates(self) -> "TaskCreateRequest":
        if self.start_date and self.due_date and self.due_date < self.start_date:
            raise ValueError("Task due_date cannot be earlier than start_date.")
        return self


class TaskUpdateRequest(BaseModel):
    """Payload for updating an existing task (id and user_story_id are immutable)."""

    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = Field(default=None, min_length=2, max_length=200)
    description: Optional[str] = Field(default=None, max_length=4000)
    assignee_id: Optional[int] = Field(default=None, ge=1)
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    start_date: Optional[date] = None
    due_date: Optional[date] = None
    estimated_hours: Optional[float] = Field(default=None, ge=0.0, le=1000.0)
    actual_hours: Optional[float] = Field(default=None, ge=0.0, le=1000.0)

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise ValueError("Task title must contain at least 2 non-whitespace characters.")
        return cleaned

    @model_validator(mode="after")
    def validate_dates(self) -> "TaskUpdateRequest":
        if self.start_date and self.due_date and self.due_date < self.start_date:
            raise ValueError("Task due_date cannot be earlier than start_date.")
        return self


class TaskStatusUpdateRequest(BaseModel):
    """Payload for PATCH /tasks/{task_id}/status (Kanban & quick status transitions)."""

    model_config = ConfigDict(extra="forbid")

    status: TaskStatus


class TaskResponse(BaseModel):
    """Task representation enriched with user story, project, and assignee context."""

    id: int
    user_story_id: int
    user_story_title: Optional[str] = None
    project_id: int
    project_name: Optional[str] = None
    title: str
    description: Optional[str]
    assignee_id: Optional[int]
    assignee_name: Optional[str] = None
    priority: TaskPriority
    status: TaskStatus
    start_date: Optional[date]
    due_date: Optional[date]
    estimated_hours: Optional[float]
    actual_hours: Optional[float]
    is_overdue: bool = False
    created_at: datetime
    updated_at: datetime


class TaskListResponse(BaseModel):
    """Paginated list of tasks."""

    items: List[TaskResponse]
    total: int
    skip: int
    limit: int
