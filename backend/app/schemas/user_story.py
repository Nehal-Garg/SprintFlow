"""User Story Pydantic schemas."""

from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

StoryPriority = Literal["Low", "Medium", "High", "Critical"]
StoryStatus = Literal["Backlog", "To Do", "In Progress", "Done"]


class UserStoryCreateRequest(BaseModel):
    """Payload for creating a user story under a project."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=2, max_length=200)
    description: Optional[str] = Field(default=None, max_length=4000)
    acceptance_criteria: Optional[str] = Field(default=None, max_length=4000)
    priority: StoryPriority = "Medium"
    status: StoryStatus = "Backlog"
    story_points: Optional[int] = Field(default=None, ge=0, le=100)
    assigned_to: Optional[int] = Field(default=None, ge=1)
    due_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise ValueError("Story title must contain at least 2 non-whitespace characters.")
        return cleaned


class UserStoryUpdateRequest(BaseModel):
    """Payload for updating an existing user story (project_id and id are immutable)."""

    model_config = ConfigDict(extra="forbid")

    title: Optional[str] = Field(default=None, min_length=2, max_length=200)
    description: Optional[str] = Field(default=None, max_length=4000)
    acceptance_criteria: Optional[str] = Field(default=None, max_length=4000)
    priority: Optional[StoryPriority] = None
    status: Optional[StoryStatus] = None
    story_points: Optional[int] = Field(default=None, ge=0, le=100)
    assigned_to: Optional[int] = Field(default=None, ge=1)
    due_date: Optional[date] = None

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise ValueError("Story title must contain at least 2 non-whitespace characters.")
        return cleaned


class UserStoryResponse(BaseModel):
    """User story representation with parent project and task completion metrics."""

    id: int
    project_id: int
    project_name: Optional[str] = None
    title: str
    description: Optional[str]
    acceptance_criteria: Optional[str]
    priority: StoryPriority
    status: StoryStatus
    story_points: Optional[int]
    assigned_to: Optional[int]
    assignee_name: Optional[str] = None
    due_date: Optional[date]
    task_count: int = 0
    completed_task_count: int = 0
    created_at: datetime
    updated_at: datetime


class UserStoryListResponse(BaseModel):
    """Paginated list of user stories for a project."""

    items: List[UserStoryResponse]
    total: int
    skip: int
    limit: int
