"""Task business logic."""

from datetime import date
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import (
    get_accessible_project_ids,
    require_project_member,
    require_story_access,
    require_task_access,
    validate_project_assignee,
)
from app.models import Task, User, UserStory
from app.schemas.task import (
    TaskCreateRequest,
    TaskListResponse,
    TaskResponse,
    TaskStatusUpdateRequest,
    TaskUpdateRequest,
)
from app.services.activity_service import record_activity
from app.services.notification_service import create_task_assignment_notification


def _serialize_task(task: Task) -> TaskResponse:
    """Build a TaskResponse enriched with story, project, assignee, and overdue status."""
    today = date.today()
    is_overdue = bool(task.due_date and task.due_date < today and task.status != "Done")
    story = task.user_story
    project = story.project if story else None

    return TaskResponse(
        id=task.id,
        user_story_id=task.user_story_id,
        user_story_title=story.title if story else None,
        project_id=story.project_id if story else 0,
        project_name=project.name if project else None,
        title=task.title,
        description=task.description,
        assignee_id=task.assignee_id,
        assignee_name=task.assignee.full_name if task.assignee else None,
        priority=task.priority,
        status=task.status,
        start_date=task.start_date,
        due_date=task.due_date,
        estimated_hours=task.estimated_hours,
        actual_hours=task.actual_hours,
        is_overdue=is_overdue,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


def _load_task_with_relations(db: Session, task_id: int) -> Task:
    return db.scalar(
        select(Task)
        .options(
            joinedload(Task.user_story).joinedload(UserStory.project),
            joinedload(Task.assignee),
        )
        .where(Task.id == task_id)
    )


def list_story_tasks(
    db: Session,
    story_id: int,
    current_user: User,
    *,
    status_filter: Optional[str] = None,
    priority: Optional[str] = None,
    assignee_id: Optional[int] = None,
    due_before: Optional[date] = None,
    due_after: Optional[date] = None,
    overdue_only: bool = False,
    skip: int = 0,
    limit: int = 100,
) -> TaskListResponse:
    """List tasks belonging to a specific user story with rich filters."""
    require_story_access(db, story_id, current_user)

    filters = [Task.user_story_id == story_id]
    if status_filter:
        filters.append(Task.status == status_filter)
    if priority:
        filters.append(Task.priority == priority)
    if assignee_id is not None:
        filters.append(Task.assignee_id == assignee_id)
    if due_before is not None:
        filters.append(Task.due_date <= due_before)
    if due_after is not None:
        filters.append(Task.due_date >= due_after)
    if overdue_only:
        filters.append(Task.due_date < date.today())
        filters.append(Task.status != "Done")

    total = db.scalar(select(func.count(Task.id)).where(*filters)) or 0
    stmt = (
        select(Task)
        .options(
            joinedload(Task.user_story).joinedload(UserStory.project),
            joinedload(Task.assignee),
        )
        .where(*filters)
        .order_by(Task.due_date.asc().nulls_last(), Task.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    tasks = list(db.scalars(stmt).all())
    return TaskListResponse(
        items=[_serialize_task(t) for t in tasks],
        total=total,
        skip=skip,
        limit=limit,
    )


def list_accessible_tasks(
    db: Session,
    current_user: User,
    *,
    project_id: Optional[int] = None,
    status_filter: Optional[str] = None,
    priority: Optional[str] = None,
    assignee_id: Optional[int] = None,
    search: Optional[str] = None,
    due_before: Optional[date] = None,
    due_after: Optional[date] = None,
    overdue_only: bool = False,
    skip: int = 0,
    limit: int = 200,
) -> TaskListResponse:
    """List tasks across projects accessible to the authenticated user (powers Kanban & search)."""
    if project_id is not None:
        require_project_member(db, project_id, current_user)
        project_ids = [project_id]
    else:
        project_ids = get_accessible_project_ids(db, current_user.id)

    if not project_ids:
        return TaskListResponse(items=[], total=0, skip=skip, limit=limit)

    filters = [UserStory.project_id.in_(project_ids)]
    if status_filter:
        filters.append(Task.status == status_filter)
    if priority:
        filters.append(Task.priority == priority)
    if assignee_id is not None:
        filters.append(Task.assignee_id == assignee_id)
    if search:
        pattern = f"%{search.strip()}%"
        filters.append(
            or_(Task.title.ilike(pattern), Task.description.ilike(pattern))
        )
    if due_before is not None:
        filters.append(Task.due_date <= due_before)
    if due_after is not None:
        filters.append(Task.due_date >= due_after)
    if overdue_only:
        filters.append(Task.due_date < date.today())
        filters.append(Task.status != "Done")

    total = (
        db.scalar(
            select(func.count(Task.id))
            .join(UserStory, Task.user_story_id == UserStory.id)
            .where(*filters)
        )
        or 0
    )

    stmt = (
        select(Task)
        .join(UserStory, Task.user_story_id == UserStory.id)
        .options(
            joinedload(Task.user_story).joinedload(UserStory.project),
            joinedload(Task.assignee),
        )
        .where(*filters)
        .order_by(Task.due_date.asc().nulls_last(), Task.updated_at.desc())
        .offset(skip)
        .limit(limit)
    )
    tasks = list(db.scalars(stmt).all())
    return TaskListResponse(
        items=[_serialize_task(t) for t in tasks],
        total=total,
        skip=skip,
        limit=limit,
    )


def list_my_tasks(
    db: Session,
    current_user: User,
    *,
    status_filter: Optional[str] = None,
    priority: Optional[str] = None,
    overdue_only: bool = False,
    skip: int = 0,
    limit: int = 100,
) -> TaskListResponse:
    """Return ONLY tasks assigned to the authenticated user inside their accessible projects."""
    return list_accessible_tasks(
        db,
        current_user,
        status_filter=status_filter,
        priority=priority,
        assignee_id=current_user.id,
        overdue_only=overdue_only,
        skip=skip,
        limit=limit,
    )


def create_task(
    db: Session,
    story_id: int,
    payload: TaskCreateRequest,
    current_user: User,
) -> TaskResponse:
    """Create a task strictly under an existing user story after authorization checks."""
    story, _ = require_story_access(db, story_id, current_user)
    assignee = validate_project_assignee(db, story.project_id, payload.assignee_id)

    task = Task(
        user_story_id=story.id,
        title=payload.title,
        description=payload.description,
        assignee_id=payload.assignee_id,
        priority=payload.priority,
        status=payload.status,
        start_date=payload.start_date,
        due_date=payload.due_date,
        estimated_hours=payload.estimated_hours,
        actual_hours=payload.actual_hours,
    )
    db.add(task)
    db.flush()

    record_activity(
        db,
        user_id=current_user.id,
        project_id=story.project_id,
        action="task_created",
        entity_type="task",
        entity_id=task.id,
        description=f"Created task '{task.title}' under story '{story.title}'",
    )

    if assignee is not None:
        record_activity(
            db,
            user_id=current_user.id,
            project_id=story.project_id,
            action="task_assigned",
            entity_type="task",
            entity_id=task.id,
            description=f"Assigned task '{task.title}' to {assignee.full_name}",
        )
        project_name = story.project.name if story.project else "SprintFlow"
        create_task_assignment_notification(
            db,
            task=task,
            project_name=project_name,
            assignee_id=assignee.id,
            assigned_by_name=current_user.full_name,
        )

    if task.status == "Done":
        record_activity(
            db,
            user_id=current_user.id,
            project_id=story.project_id,
            action="task_completed",
            entity_type="task",
            entity_id=task.id,
            description=f"Completed task '{task.title}'",
        )

    db.commit()
    return _serialize_task(_load_task_with_relations(db, task.id))


def get_task(
    db: Session,
    task_id: int,
    current_user: User,
) -> TaskResponse:
    """Retrieve a single task after verifying parent project membership."""
    task, _ = require_task_access(db, task_id, current_user)
    return _serialize_task(task)


def update_task(
    db: Session,
    task_id: int,
    payload: TaskUpdateRequest,
    current_user: User,
) -> TaskResponse:
    """Update a task while keeping id and user_story_id immutable."""
    task, _ = require_task_access(db, task_id, current_user)
    project_id = task.user_story.project_id
    fields_set = payload.model_fields_set

    new_start = payload.start_date if "start_date" in fields_set else task.start_date
    new_due = payload.due_date if "due_date" in fields_set else task.due_date
    if new_start and new_due and new_due < new_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Task due_date cannot be earlier than start_date.",
        )

    previous_assignee_id = task.assignee_id
    previous_status = task.status

    new_assignee = None
    if "assignee_id" in fields_set:
        new_assignee = validate_project_assignee(db, project_id, payload.assignee_id)

    for field in (
        "title",
        "description",
        "assignee_id",
        "priority",
        "status",
        "start_date",
        "due_date",
        "estimated_hours",
        "actual_hours",
    ):
        if field in fields_set:
            value = getattr(payload, field)
            if field in ("title", "priority", "status") and value is None:
                continue
            setattr(task, field, value)

    record_activity(
        db,
        user_id=current_user.id,
        project_id=project_id,
        action="task_updated",
        entity_type="task",
        entity_id=task.id,
        description=f"Updated task '{task.title}'",
    )

    if "assignee_id" in fields_set and task.assignee_id != previous_assignee_id and new_assignee is not None:
        record_activity(
            db,
            user_id=current_user.id,
            project_id=project_id,
            action="task_assigned",
            entity_type="task",
            entity_id=task.id,
            description=f"Assigned task '{task.title}' to {new_assignee.full_name}",
        )
        project_name = (
            task.user_story.project.name
            if task.user_story and task.user_story.project
            else "SprintFlow"
        )
        create_task_assignment_notification(
            db,
            task=task,
            project_name=project_name,
            assignee_id=new_assignee.id,
            assigned_by_name=current_user.full_name,
        )

    if task.status != previous_status:
        record_activity(
            db,
            user_id=current_user.id,
            project_id=project_id,
            action="task_status_changed",
            entity_type="task",
            entity_id=task.id,
            description=f"Changed task '{task.title}' status from '{previous_status}' to '{task.status}'",
        )
        if task.status == "Done":
            record_activity(
                db,
                user_id=current_user.id,
                project_id=project_id,
                action="task_completed",
                entity_type="task",
                entity_id=task.id,
                description=f"Completed task '{task.title}'",
            )

    db.commit()
    return _serialize_task(_load_task_with_relations(db, task.id))


def update_task_status(
    db: Session,
    task_id: int,
    payload: TaskStatusUpdateRequest,
    current_user: User,
) -> TaskResponse:
    """Transition a task's status (used by Kanban drag-and-drop and quick status controls)."""
    task, _ = require_task_access(db, task_id, current_user)
    project_id = task.user_story.project_id
    previous_status = task.status

    if previous_status != payload.status:
        task.status = payload.status
        record_activity(
            db,
            user_id=current_user.id,
            project_id=project_id,
            action="task_status_changed",
            entity_type="task",
            entity_id=task.id,
            description=f"Changed task '{task.title}' status from '{previous_status}' to '{task.status}'",
        )
        if task.status == "Done":
            record_activity(
                db,
                user_id=current_user.id,
                project_id=project_id,
                action="task_completed",
                entity_type="task",
                entity_id=task.id,
                description=f"Completed task '{task.title}'",
            )
        db.commit()

    return _serialize_task(_load_task_with_relations(db, task.id))


def delete_task(
    db: Session,
    task_id: int,
    current_user: User,
) -> None:
    """Delete a task after verifying parent project membership."""
    task, _ = require_task_access(db, task_id, current_user)
    project_id = task.user_story.project_id
    task_title = task.title
    task_pk = task.id

    record_activity(
        db,
        user_id=current_user.id,
        project_id=project_id,
        action="task_deleted",
        entity_type="task",
        entity_id=task_pk,
        description=f"Deleted task '{task_title}'",
    )
    db.delete(task)
    db.commit()
