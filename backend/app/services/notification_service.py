"""Persistent notification service and background job log queries."""

import logging
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.dependencies import get_accessible_project_ids
from app.models import BackgroundJobLog, Notification, Task, User, UserStory
from app.schemas.notification import (
    BackgroundJobLogResponse,
    NotificationListResponse,
    NotificationReadAllResponse,
    NotificationResponse,
)

logger = logging.getLogger("sprintflow.notifications")


def create_task_assignment_notification(
    db: Session,
    *,
    task: Task,
    project_name: str,
    assignee_id: int,
    assigned_by_name: str,
) -> Optional[Notification]:
    """Persist a task_assignment notification safely with deduplication protection.

    Uses a per-assignment revision counter so reassigning a task notifies the assignee
    while avoiding duplicate alerts during unrelated edits. Never raises to break task saves.
    """
    try:
        # Avoid duplicate unread assignment alerts for the exact same (user, task)
        existing_unread = db.scalar(
            select(Notification).where(
                Notification.user_id == assignee_id,
                Notification.task_id == task.id,
                Notification.notification_type == "task_assignment",
                Notification.is_read.is_(False),
            )
        )
        if existing_unread is not None:
            return existing_unread

        prior_count = (
            db.scalar(
                select(func.count(Notification.id)).where(
                    Notification.user_id == assignee_id,
                    Notification.task_id == task.id,
                    Notification.notification_type == "task_assignment",
                )
            )
            or 0
        )
        dedup_key = (
            f"task_assignment:task:{task.id}:user:{assignee_id}:rev:{prior_count + 1}"
        )
        message = (
            f"You were assigned task '{task.title}' in project '{project_name}' "
            f"by {assigned_by_name}."
        )
        notification = Notification(
            user_id=assignee_id,
            task_id=task.id,
            message=message,
            notification_type="task_assignment",
            dedup_key=dedup_key,
            is_read=False,
        )
        db.add(notification)
        return notification
    except Exception as exc:  # pragma: no cover - defensive guard
        logger.warning("Failed to queue task assignment notification: %s", type(exc).__name__)
        return None


def list_notifications(
    db: Session,
    current_user: User,
    *,
    unread_only: bool = False,
    notification_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> NotificationListResponse:
    """List persistent notifications strictly belonging to the authenticated user."""
    filters = [Notification.user_id == current_user.id]
    if unread_only:
        filters.append(Notification.is_read.is_(False))
    if notification_type:
        filters.append(Notification.notification_type == notification_type)

    total = db.scalar(select(func.count(Notification.id)).where(*filters)) or 0
    unread_count = (
        db.scalar(
            select(func.count(Notification.id)).where(
                Notification.user_id == current_user.id,
                Notification.is_read.is_(False),
            )
        )
        or 0
    )

    stmt = (
        select(Notification)
        .where(*filters)
        .order_by(Notification.created_at.desc(), Notification.id.desc())
        .offset(skip)
        .limit(limit)
    )
    rows = list(db.scalars(stmt).all())
    return NotificationListResponse(
        items=[NotificationResponse.model_validate(row) for row in rows],
        total=total,
        unread_count=unread_count,
        skip=skip,
        limit=limit,
    )


def mark_notification_read(
    db: Session,
    notification_id: int,
    current_user: User,
) -> NotificationResponse:
    """Mark a single notification as read after verifying ownership."""
    notification = db.get(Notification, notification_id)
    if notification is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification {notification_id} not found.",
        )
    if notification.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to modify this notification.",
        )

    if not notification.is_read:
        notification.is_read = True
        db.commit()
        db.refresh(notification)

    return NotificationResponse.model_validate(notification)


def mark_all_notifications_read(
    db: Session,
    current_user: User,
) -> NotificationReadAllResponse:
    """Mark every unread notification for the authenticated user as read."""
    result = db.execute(
        update(Notification)
        .where(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
        .values(is_read=True)
    )
    db.commit()
    updated = result.rowcount or 0
    return NotificationReadAllResponse(
        updated_count=updated,
        message=f"Marked {updated} notification(s) as read.",
    )


def list_background_job_logs(
    db: Session,
    current_user: User,
    *,
    limit: int = 30,
) -> List[BackgroundJobLogResponse]:
    """List recent background reminder job logs for tasks inside the user's projects."""
    accessible_ids = get_accessible_project_ids(db, current_user.id)
    if not accessible_ids:
        return []

    stmt = (
        select(BackgroundJobLog)
        .join(Task, BackgroundJobLog.task_id == Task.id)
        .join(UserStory, Task.user_story_id == UserStory.id)
        .where(UserStory.project_id.in_(accessible_ids))
        .order_by(BackgroundJobLog.created_at.desc(), BackgroundJobLog.id.desc())
        .limit(limit)
    )
    rows = list(db.scalars(stmt).all())
    return [BackgroundJobLogResponse.model_validate(row) for row in rows]
