"""User Story business logic."""

from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import (
    require_project_member,
    require_story_access,
    validate_project_assignee,
)
from app.models import Task, User, UserStory
from app.schemas.user_story import (
    UserStoryCreateRequest,
    UserStoryListResponse,
    UserStoryResponse,
    UserStoryUpdateRequest,
)
from app.services.activity_service import record_activity


def _serialize_story(db: Session, story: UserStory) -> UserStoryResponse:
    """Build a UserStoryResponse with live child task counts."""
    task_count = (
        db.scalar(select(func.count(Task.id)).where(Task.user_story_id == story.id))
        or 0
    )
    completed_task_count = (
        db.scalar(
            select(func.count(Task.id)).where(
                Task.user_story_id == story.id,
                Task.status == "Done",
            )
        )
        or 0
    )

    return UserStoryResponse(
        id=story.id,
        project_id=story.project_id,
        project_name=story.project.name if story.project else None,
        title=story.title,
        description=story.description,
        acceptance_criteria=story.acceptance_criteria,
        priority=story.priority,
        status=story.status,
        story_points=story.story_points,
        assigned_to=story.assigned_to,
        assignee_name=story.assignee.full_name if story.assignee else None,
        due_date=story.due_date,
        task_count=task_count,
        completed_task_count=completed_task_count,
        created_at=story.created_at,
        updated_at=story.updated_at,
    )


def list_project_stories(
    db: Session,
    project_id: int,
    current_user: User,
    *,
    priority: Optional[str] = None,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> UserStoryListResponse:
    """List user stories inside an authorized project with priority/status/search filters."""
    require_project_member(db, project_id, current_user)

    filters = [UserStory.project_id == project_id]
    if priority:
        filters.append(UserStory.priority == priority)
    if status_filter:
        filters.append(UserStory.status == status_filter)
    if search:
        pattern = f"%{search.strip()}%"
        filters.append(
            or_(
                UserStory.title.ilike(pattern),
                UserStory.description.ilike(pattern),
            )
        )

    total = db.scalar(select(func.count(UserStory.id)).where(*filters)) or 0
    stmt = (
        select(UserStory)
        .options(joinedload(UserStory.project), joinedload(UserStory.assignee))
        .where(*filters)
        .order_by(UserStory.updated_at.desc(), UserStory.id.desc())
        .offset(skip)
        .limit(limit)
    )
    stories = list(db.scalars(stmt).all())
    items = [_serialize_story(db, story) for story in stories]
    return UserStoryListResponse(items=items, total=total, skip=skip, limit=limit)


def create_story(
    db: Session,
    project_id: int,
    payload: UserStoryCreateRequest,
    current_user: User,
) -> UserStoryResponse:
    """Create a user story strictly under an existing authorized project."""
    project, _ = require_project_member(db, project_id, current_user)
    validate_project_assignee(db, project.id, payload.assigned_to)

    story = UserStory(
        project_id=project.id,
        title=payload.title,
        description=payload.description,
        acceptance_criteria=payload.acceptance_criteria,
        priority=payload.priority,
        status=payload.status,
        story_points=payload.story_points,
        assigned_to=payload.assigned_to,
        due_date=payload.due_date,
    )
    db.add(story)
    db.flush()

    record_activity(
        db,
        user_id=current_user.id,
        project_id=project.id,
        action="story_created",
        entity_type="user_story",
        entity_id=story.id,
        description=f"Created user story '{story.title}' in project '{project.name}'",
    )

    db.commit()
    loaded = db.scalar(
        select(UserStory)
        .options(joinedload(UserStory.project), joinedload(UserStory.assignee))
        .where(UserStory.id == story.id)
    )
    return _serialize_story(db, loaded)


def get_story(
    db: Session,
    story_id: int,
    current_user: User,
) -> UserStoryResponse:
    """Retrieve a single user story after verifying parent project membership."""
    story, _ = require_story_access(db, story_id, current_user)
    return _serialize_story(db, story)


def update_story(
    db: Session,
    story_id: int,
    payload: UserStoryUpdateRequest,
    current_user: User,
) -> UserStoryResponse:
    """Update a user story while keeping project_id immutable and validating membership."""
    story, _ = require_story_access(db, story_id, current_user)
    fields_set = payload.model_fields_set

    if "assigned_to" in fields_set:
        validate_project_assignee(db, story.project_id, payload.assigned_to)

    for field in (
        "title",
        "description",
        "acceptance_criteria",
        "priority",
        "status",
        "story_points",
        "assigned_to",
        "due_date",
    ):
        if field in fields_set:
            value = getattr(payload, field)
            if field in ("title", "priority", "status") and value is None:
                continue
            setattr(story, field, value)

    record_activity(
        db,
        user_id=current_user.id,
        project_id=story.project_id,
        action="story_updated",
        entity_type="user_story",
        entity_id=story.id,
        description=f"Updated user story '{story.title}'",
    )

    db.commit()
    loaded = db.scalar(
        select(UserStory)
        .options(joinedload(UserStory.project), joinedload(UserStory.assignee))
        .where(UserStory.id == story.id)
    )
    return _serialize_story(db, loaded)


def delete_story(
    db: Session,
    story_id: int,
    current_user: User,
) -> None:
    """Delete a user story and cascade-delete its child tasks."""
    story, _ = require_story_access(db, story_id, current_user)
    story_title = story.title
    story_pk = story.id
    project_id = story.project_id

    record_activity(
        db,
        user_id=current_user.id,
        project_id=project_id,
        action="story_deleted",
        entity_type="user_story",
        entity_id=story_pk,
        description=f"Deleted user story '{story_title}'",
    )
    db.delete(story)
    db.commit()
