"""Task CRUD, status transition, and background deadline reminder scheduling routes."""

from datetime import date
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.background.deadline_reminders import process_task_deadline_reminder
from app.core.dependencies import get_current_user, get_db, get_session_factory
from app.models import User
from app.schemas.task import (
    TaskCreateRequest,
    TaskListResponse,
    TaskPriority,
    TaskResponse,
    TaskStatus,
    TaskStatusUpdateRequest,
    TaskUpdateRequest,
)
from app.services import task_service

router = APIRouter(tags=["Tasks"])


@router.get(
    "/stories/{story_id}/tasks",
    response_model=TaskListResponse,
    status_code=status.HTTP_200_OK,
    summary="List tasks under a specific user story",
)
def list_story_tasks(
    story_id: int,
    status_filter: Optional[TaskStatus] = Query(default=None, alias="status"),
    priority: Optional[TaskPriority] = Query(default=None),
    assignee_id: Optional[int] = Query(default=None, ge=1),
    due_before: Optional[date] = Query(default=None),
    due_after: Optional[date] = Query(default=None),
    overdue_only: bool = Query(default=False),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskListResponse:
    return task_service.list_story_tasks(
        db,
        story_id,
        current_user,
        status_filter=status_filter,
        priority=priority,
        assignee_id=assignee_id,
        due_before=due_before,
        due_after=due_after,
        overdue_only=overdue_only,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/stories/{story_id}/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task under an existing user story and schedule deadline check",
)
def create_task(
    story_id: int,
    payload: TaskCreateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    session_factory=Depends(get_session_factory),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    task = task_service.create_task(db, story_id, payload, current_user)
    background_tasks.add_task(
        process_task_deadline_reminder,
        task.id,
        session_factory=session_factory,
    )
    return task


@router.get(
    "/tasks",
    response_model=TaskListResponse,
    status_code=status.HTTP_200_OK,
    summary="List tasks across projects accessible to the authenticated user",
)
def list_tasks(
    project_id: Optional[int] = Query(default=None, ge=1),
    status_filter: Optional[TaskStatus] = Query(default=None, alias="status"),
    priority: Optional[TaskPriority] = Query(default=None),
    assignee_id: Optional[int] = Query(default=None, ge=1),
    search: Optional[str] = Query(default=None, max_length=200),
    due_before: Optional[date] = Query(default=None),
    due_after: Optional[date] = Query(default=None),
    overdue_only: bool = Query(default=False),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=200, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskListResponse:
    return task_service.list_accessible_tasks(
        db,
        current_user,
        project_id=project_id,
        status_filter=status_filter,
        priority=priority,
        assignee_id=assignee_id,
        search=search,
        due_before=due_before,
        due_after=due_after,
        overdue_only=overdue_only,
        skip=skip,
        limit=limit,
    )


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Get task details",
)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    return task_service.get_task(db, task_id, current_user)


@router.put(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Update task details and schedule background deadline check",
)
def update_task(
    task_id: int,
    payload: TaskUpdateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    session_factory=Depends(get_session_factory),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    task = task_service.update_task(db, task_id, payload, current_user)
    background_tasks.add_task(
        process_task_deadline_reminder,
        task.id,
        session_factory=session_factory,
    )
    return task


@router.patch(
    "/tasks/{task_id}/status",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a task's workflow status and re-evaluate deadline reminders asynchronously",
)
def patch_task_status(
    task_id: int,
    payload: TaskStatusUpdateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    session_factory=Depends(get_session_factory),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    task = task_service.update_task_status(db, task_id, payload, current_user)
    background_tasks.add_task(
        process_task_deadline_reminder,
        task.id,
        session_factory=session_factory,
    )
    return task


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    task_service.delete_task(db, task_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
