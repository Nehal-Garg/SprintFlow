"""Project and ProjectMember Pydantic schemas."""

from datetime import date, datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ProjectStatus = Literal["Planning", "Active", "On Hold", "Completed"]
ProjectMemberRole = Literal["owner", "member"]


class ProjectCreateRequest(BaseModel):
    """Payload for creating a new project."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=2, max_length=150)
    description: Optional[str] = Field(default=None, max_length=2000)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: ProjectStatus = "Planning"

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise ValueError("Project name must contain at least 2 non-whitespace characters.")
        return cleaned

    @model_validator(mode="after")
    def validate_dates(self) -> "ProjectCreateRequest":
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("Project end_date cannot be earlier than start_date.")
        return self


class ProjectUpdateRequest(BaseModel):
    """Payload for updating an existing project (id and created_by cannot be modified)."""

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    description: Optional[str] = Field(default=None, max_length=2000)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[ProjectStatus] = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return None
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise ValueError("Project name must contain at least 2 non-whitespace characters.")
        return cleaned

    @model_validator(mode="after")
    def validate_dates(self) -> "ProjectUpdateRequest":
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("Project end_date cannot be earlier than start_date.")
        return self


class ProjectMemberAddRequest(BaseModel):
    """Payload for adding a team member to a project."""

    model_config = ConfigDict(extra="forbid")

    user_id: int = Field(..., ge=1)
    role: ProjectMemberRole = "member"


class ProjectMemberResponse(BaseModel):
    """Project member details."""

    id: int
    user_id: int
    full_name: str
    email: str
    role: ProjectMemberRole
    joined_at: datetime


class ProjectResponse(BaseModel):
    """Project response enriched with real-time progress and membership metadata."""

    id: int
    name: str
    description: Optional[str]
    start_date: Optional[date]
    end_date: Optional[date]
    status: ProjectStatus
    created_by: int
    creator_name: Optional[str] = None
    current_user_role: ProjectMemberRole
    progress: float
    story_count: int
    task_count: int
    completed_task_count: int
    members: List[ProjectMemberResponse]
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    """Paginated list of accessible projects."""

    items: List[ProjectResponse]
    total: int
    skip: int
    limit: int
