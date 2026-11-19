"""My Tasks route scoped strictly to the authenticated user."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.task import TaskListResponse, TaskPriority, TaskStatus
from app.services import task_service

router = APIRouter(tags=["My Tasks"])


@router.get(
    "/my-tasks",
    response_model=TaskListResponse,
    status_code=status.HTTP_200_OK,
    summary="List tasks assigned specifically to the authenticated user",
)
def get_my_tasks(
    status_filter: Optional[TaskStatus] = Query(default=None, alias="status"),
    priority: Optional[TaskPriority] = Query(default=None),
    overdue_only: bool = Query(default=False),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskListResponse:
    return task_service.list_my_tasks(
        db,
        current_user,
        status_filter=status_filter,
        priority=priority,
        overdue_only=overdue_only,
        skip=skip,
        limit=limit,
    )
