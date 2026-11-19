"""Chronological activity log routes."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.activity import ActivityEntityType, ActivityLogListResponse
from app.services import activity_service

router = APIRouter(prefix="/activity", tags=["Activity Log"])


@router.get(
    "",
    response_model=ActivityLogListResponse,
    status_code=status.HTTP_200_OK,
    summary="List chronological activity logs scoped to the user's accessible projects",
)
def list_activity(
    project_id: Optional[int] = Query(default=None, ge=1),
    entity_type: Optional[ActivityEntityType] = Query(default=None),
    action: Optional[str] = Query(default=None, max_length=50),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ActivityLogListResponse:
    return activity_service.list_activities(
        db,
        current_user,
        project_id=project_id,
        entity_type=entity_type,
        action=action,
        skip=skip,
        limit=limit,
    )
