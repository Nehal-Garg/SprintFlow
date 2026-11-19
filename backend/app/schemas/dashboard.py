"""Dashboard analytics and project progress Pydantic schemas."""

from datetime import date
from typing import List, Optional

from pydantic import BaseModel

from app.schemas.activity import ActivityLogResponse
from app.schemas.project import ProjectResponse
from app.schemas.task import TaskResponse


class StatusCountItem(BaseModel):
    """Task count grouped by workflow status."""

    status: str
    count: int


class PriorityCountItem(BaseModel):
    """Task count grouped by priority."""

    priority: str
    count: int


class ProjectProgressItem(BaseModel):
    """Task completion percentage for a single project."""

    project_id: int
    project_name: str
    status: str
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    progress: float
    end_date: Optional[date] = None


class ProjectProgressResponse(BaseModel):
    """List of project progress metrics."""

    items: List[ProjectProgressItem]


class DashboardSummaryResponse(BaseModel):
    """Comprehensive live dashboard payload computed dynamically from SQLite."""

    total_projects: int
    active_projects: int
    completed_projects: int
    total_stories: int
    total_tasks: int
    completed_tasks: int
    pending_tasks: int
    overdue_tasks: int
    tasks_by_status: List[StatusCountItem]
    tasks_by_priority: List[PriorityCountItem]
    project_progress: List[ProjectProgressItem]
    recent_projects: List[ProjectResponse]
    recent_activity: List[ActivityLogResponse]
    upcoming_deadlines: List[TaskResponse]
    overdue_task_list: List[TaskResponse]
    recently_updated_tasks: List[TaskResponse]
    my_assigned_tasks: List[TaskResponse]
