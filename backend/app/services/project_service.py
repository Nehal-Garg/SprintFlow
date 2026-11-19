"""Project and project membership business logic."""

from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import (
    get_accessible_project_ids,
    get_project_membership,
    require_project_member,
    require_project_owner,
)
from app.models import Project, ProjectMember, Task, User, UserStory
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectListResponse,
    ProjectMemberAddRequest,
    ProjectMemberResponse,
    ProjectResponse,
    ProjectUpdateRequest,
)
from app.services.activity_service import record_activity


def _serialize_project(
    db: Session,
    project: Project,
    current_user_id: int,
) -> ProjectResponse:
    """Build an enriched ProjectResponse with live task progress and members."""
    members_stmt = (
        select(ProjectMember)
        .options(joinedload(ProjectMember.user))
        .where(ProjectMember.project_id == project.id)
        .order_by(ProjectMember.role.desc(), ProjectMember.joined_at.asc())
    )
    member_rows = list(db.scalars(members_stmt).all())

    current_role = "member"
    members_payload: List[ProjectMemberResponse] = []
    for row in member_rows:
        if row.user_id == current_user_id:
            current_role = row.role
        members_payload.append(
            ProjectMemberResponse(
                id=row.id,
                user_id=row.user_id,
                full_name=row.user.full_name,
                email=row.user.email,
                role=row.role,
                joined_at=row.joined_at,
            )
        )

    story_count = (
        db.scalar(
            select(func.count(UserStory.id)).where(UserStory.project_id == project.id)
        )
        or 0
    )

    task_count = (
        db.scalar(
            select(func.count(Task.id))
            .join(UserStory, Task.user_story_id == UserStory.id)
            .where(UserStory.project_id == project.id)
        )
        or 0
    )

    completed_task_count = (
        db.scalar(
            select(func.count(Task.id))
            .join(UserStory, Task.user_story_id == UserStory.id)
            .where(UserStory.project_id == project.id, Task.status == "Done")
        )
        or 0
    )

    progress = round((completed_task_count / task_count) * 100.0, 1) if task_count > 0 else 0.0
    creator_name = project.creator.full_name if project.creator else None

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        start_date=project.start_date,
        end_date=project.end_date,
        status=project.status,
        created_by=project.created_by,
        creator_name=creator_name,
        current_user_role=current_role,
        progress=progress,
        story_count=story_count,
        task_count=task_count,
        completed_task_count=completed_task_count,
        members=members_payload,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


def create_project(
    db: Session,
    payload: ProjectCreateRequest,
    current_user: User,
) -> ProjectResponse:
    """Create a project, enroll the creator as owner, and log activity."""
    project = Project(
        name=payload.name,
        description=payload.description,
        start_date=payload.start_date,
        end_date=payload.end_date,
        status=payload.status,
        created_by=current_user.id,
    )
    db.add(project)
    db.flush()

    owner_membership = ProjectMember(
        project_id=project.id,
        user_id=current_user.id,
        role="owner",
    )
    db.add(owner_membership)

    record_activity(
        db,
        user_id=current_user.id,
        project_id=project.id,
        action="project_created",
        entity_type="project",
        entity_id=project.id,
        description=f"Created project '{project.name}'",
    )

    db.commit()
    db.refresh(project)
    return _serialize_project(db, project, current_user.id)


def list_projects(
    db: Session,
    current_user: User,
    *,
    search: Optional[str] = None,
    status_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> ProjectListResponse:
    """List only projects the authenticated user belongs to, with search and status filtering."""
    accessible_ids = get_accessible_project_ids(db, current_user.id)
    if not accessible_ids:
        return ProjectListResponse(items=[], total=0, skip=skip, limit=limit)

    filters = [Project.id.in_(accessible_ids)]
    if status_filter:
        filters.append(Project.status == status_filter)
    if search:
        pattern = f"%{search.strip()}%"
        filters.append(
            or_(
                Project.name.ilike(pattern),
                Project.description.ilike(pattern),
            )
        )

    total = db.scalar(select(func.count(Project.id)).where(*filters)) or 0
    stmt = (
        select(Project)
        .options(joinedload(Project.creator))
        .where(*filters)
        .order_by(Project.updated_at.desc(), Project.id.desc())
        .offset(skip)
        .limit(limit)
    )
    projects = list(db.scalars(stmt).all())
    items = [_serialize_project(db, project, current_user.id) for project in projects]
    return ProjectListResponse(items=items, total=total, skip=skip, limit=limit)


def get_project(
    db: Session,
    project_id: int,
    current_user: User,
) -> ProjectResponse:
    """Fetch a single project after verifying membership."""
    project, _ = require_project_member(db, project_id, current_user)
    return _serialize_project(db, project, current_user.id)


def update_project(
    db: Session,
    project_id: int,
    payload: ProjectUpdateRequest,
    current_user: User,
) -> ProjectResponse:
    """Update a project after verifying membership and merged date integrity."""
    project, _ = require_project_member(db, project_id, current_user)

    fields_set = payload.model_fields_set
    new_start = payload.start_date if "start_date" in fields_set else project.start_date
    new_end = payload.end_date if "end_date" in fields_set else project.end_date
    if new_start and new_end and new_end < new_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project end_date cannot be earlier than start_date.",
        )

    for field in ("name", "description", "start_date", "end_date", "status"):
        if field in fields_set:
            value = getattr(payload, field)
            if field in ("name", "status") and value is None:
                continue
            setattr(project, field, value)

    record_activity(
        db,
        user_id=current_user.id,
        project_id=project.id,
        action="project_updated",
        entity_type="project",
        entity_id=project.id,
        description=f"Updated project '{project.name}'",
    )

    db.commit()
    db.refresh(project)
    return _serialize_project(db, project, current_user.id)


def delete_project(
    db: Session,
    project_id: int,
    current_user: User,
) -> None:
    """Delete a project (owner-only), cascading members, user stories, and tasks."""
    project, _ = require_project_owner(db, project_id, current_user)
    project_name = project.name
    project_pk = project.id

    record_activity(
        db,
        user_id=current_user.id,
        project_id=None,
        action="project_deleted",
        entity_type="project",
        entity_id=project_pk,
        description=f"Deleted project '{project_name}'",
    )
    db.delete(project)
    db.commit()


def add_project_member(
    db: Session,
    project_id: int,
    payload: ProjectMemberAddRequest,
    current_user: User,
) -> ProjectMemberResponse:
    """Add an existing registered user to a project (owner-only)."""
    project, _ = require_project_owner(db, project_id, current_user)

    target_user = db.get(User, payload.user_id)
    if target_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {payload.user_id} not found.",
        )

    existing = get_project_membership(db, project.id, target_user.id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this project.",
        )

    membership = ProjectMember(
        project_id=project.id,
        user_id=target_user.id,
        role=payload.role,
    )
    db.add(membership)
    record_activity(
        db,
        user_id=current_user.id,
        project_id=project.id,
        action="project_updated",
        entity_type="project",
        entity_id=project.id,
        description=f"Added {target_user.full_name} to project '{project.name}' as {payload.role}",
    )
    db.commit()
    db.refresh(membership)

    return ProjectMemberResponse(
        id=membership.id,
        user_id=target_user.id,
        full_name=target_user.full_name,
        email=target_user.email,
        role=membership.role,
        joined_at=membership.joined_at,
    )


def remove_project_member(
    db: Session,
    project_id: int,
    user_id: int,
    current_user: User,
) -> None:
    """Remove a member from a project (owner-only) while protecting the last owner."""
    project, _ = require_project_owner(db, project_id, current_user)

    membership = get_project_membership(db, project.id, user_id)
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not a member of this project.",
        )

    if membership.role == "owner":
        owner_count = (
            db.scalar(
                select(func.count(ProjectMember.id)).where(
                    ProjectMember.project_id == project.id,
                    ProjectMember.role == "owner",
                )
            )
            or 0
        )
        if owner_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the last remaining owner of a project.",
            )

    # Clear assignments inside this project to preserve membership-assignment integrity
    story_ids = list(
        db.scalars(select(UserStory.id).where(UserStory.project_id == project.id)).all()
    )
    if story_ids:
        for story in db.scalars(
            select(UserStory).where(
                UserStory.project_id == project.id,
                UserStory.assigned_to == user_id,
            )
        ).all():
            story.assigned_to = None

        for task in db.scalars(
            select(Task).where(
                Task.user_story_id.in_(story_ids),
                Task.assignee_id == user_id,
            )
        ).all():
            task.assignee_id = None

    removed_user = db.get(User, user_id)
    removed_name = removed_user.full_name if removed_user else f"User #{user_id}"

    db.delete(membership)
    record_activity(
        db,
        user_id=current_user.id,
        project_id=project.id,
        action="project_updated",
        entity_type="project",
        entity_id=project.id,
        description=f"Removed {removed_name} from project '{project.name}'",
    )
    db.commit()
