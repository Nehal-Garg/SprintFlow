"""Activity logging helper and chronological query service."""

from typing import Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import get_accessible_project_ids, require_project_member
from app.models import ActivityLog, User
from app.schemas.activity import ActivityLogListResponse, ActivityLogResponse


def record_activity(
    db: Session,
    *,
    user_id: Optional[int],
    project_id: Optional[int],
    action: str,
    entity_type: str,
    entity_id: int,
    description: str,
) -> ActivityLog:
    """Append an ActivityLog entry to the active SQLAlchemy session."""
    entry = ActivityLog(
        user_id=user_id,
        project_id=project_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        description=description,
    )
    db.add(entry)
    return entry


def serialize_activity(entry: ActivityLog) -> ActivityLogResponse:
    """Convert an ActivityLog ORM instance into a public response schema."""
    return ActivityLogResponse(
        id=entry.id,
        user_id=entry.user_id,
        user_name=entry.user.full_name if entry.user else "System",
        project_id=entry.project_id,
        project_name=entry.project.name if entry.project else None,
        action=entry.action,
        entity_type=entry.entity_type,
        entity_id=entry.entity_id,
        description=entry.description,
        created_at=entry.created_at,
    )


def list_activities(
    db: Session,
    current_user: User,
    *,
    project_id: Optional[int] = None,
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> ActivityLogListResponse:
    """Return chronological activity logs scoped strictly to the user's accessible projects."""
    if project_id is not None:
        require_project_member(db, project_id, current_user)
        scope_filter = ActivityLog.project_id == project_id
    else:
        accessible_ids = get_accessible_project_ids(db, current_user.id)
        if accessible_ids:
            scope_filter = or_(
                ActivityLog.project_id.in_(accessible_ids),
                and_(
                    ActivityLog.project_id.is_(None),
                    ActivityLog.user_id == current_user.id,
                ),
            )
        else:
            scope_filter = and_(
                ActivityLog.project_id.is_(None),
                ActivityLog.user_id == current_user.id,
            )

    filters = [scope_filter]
    if entity_type:
        filters.append(ActivityLog.entity_type == entity_type)
    if action:
        filters.append(ActivityLog.action == action)

    total = db.scalar(select(func.count(ActivityLog.id)).where(*filters)) or 0
    stmt = (
        select(ActivityLog)
        .options(joinedload(ActivityLog.user), joinedload(ActivityLog.project))
        .where(*filters)
        .order_by(ActivityLog.created_at.desc(), ActivityLog.id.desc())
        .offset(skip)
        .limit(limit)
    )
    rows = list(db.scalars(stmt).all())
    return ActivityLogListResponse(
        items=[serialize_activity(row) for row in rows],
        total=total,
        skip=skip,
        limit=limit,
    )
