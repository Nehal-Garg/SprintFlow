"""Persistent user notification routes."""

from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.notification import (
    BackgroundJobLogResponse,
    NotificationListResponse,
    NotificationReadAllResponse,
    NotificationResponse,
    NotificationType,
)
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get(
    "",
    response_model=NotificationListResponse,
    status_code=status.HTTP_200_OK,
    summary="List persistent notifications for the authenticated user",
)
def list_notifications(
    unread_only: bool = Query(default=False),
    notification_type: Optional[NotificationType] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationListResponse:
    return notification_service.list_notifications(
        db,
        current_user,
        unread_only=unread_only,
        notification_type=notification_type,
        skip=skip,
        limit=limit,
    )


@router.patch(
    "/read-all",
    response_model=NotificationReadAllResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark all unread notifications as read for the authenticated user",
)
def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationReadAllResponse:
    return notification_service.mark_all_notifications_read(db, current_user)


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark a single notification as read (owner only)",
)
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationResponse:
    return notification_service.mark_notification_read(db, notification_id, current_user)


@router.get(
    "/job-logs",
    response_model=List[BackgroundJobLogResponse],
    status_code=status.HTTP_200_OK,
    summary="Inspect recent background reminder execution logs for accessible projects",
)
def get_background_job_logs(
    limit: int = Query(default=25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[BackgroundJobLogResponse]:
    return notification_service.list_background_job_logs(db, current_user, limit=limit)
