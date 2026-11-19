"""Dynamic dashboard analytics and project progress aggregation service."""

from datetime import date, timedelta
from typing import List

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import get_accessible_project_ids
from app.models import Project, Task, User, UserStory
from app.models.task import TASK_PRIORITIES, TASK_STATUSES
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    PriorityCountItem,
    ProjectProgressItem,
    ProjectProgressResponse,
    StatusCountItem,
)
from app.services.activity_service import list_activities
from app.services.project_service import _serialize_project
from app.services.task_service import _serialize_task


def get_project_progress_items(
    db: Session,
    current_user: User,
) -> List[ProjectProgressItem]:
    """Calculate live task completion percentages for every accessible project."""
    accessible_ids = get_accessible_project_ids(db, current_user.id)
    if not accessible_ids:
        return []

    projects = list(
        db.scalars(
            select(Project)
            .where(Project.id.in_(accessible_ids))
            .order_by(Project.updated_at.desc(), Project.id.desc())
        ).all()
    )

    items: List[ProjectProgressItem] = []
    for project in projects:
        total_tasks = (
            db.scalar(
                select(func.count(Task.id))
                .join(UserStory, Task.user_story_id == UserStory.id)
                .where(UserStory.project_id == project.id)
            )
            or 0
        )
        completed_tasks = (
            db.scalar(
                select(func.count(Task.id))
                .join(UserStory, Task.user_story_id == UserStory.id)
                .where(UserStory.project_id == project.id, Task.status == "Done")
            )
            or 0
        )
        pending_tasks = total_tasks - completed_tasks
        progress = round((completed_tasks / total_tasks) * 100.0, 1) if total_tasks > 0 else 0.0
        items.append(
            ProjectProgressItem(
                project_id=project.id,
                project_name=project.name,
                status=project.status,
                total_tasks=total_tasks,
                completed_tasks=completed_tasks,
                pending_tasks=pending_tasks,
                progress=progress,
                end_date=project.end_date,
            )
        )
    return items


def get_project_progress(db: Session, current_user: User) -> ProjectProgressResponse:
    """Return wrapped project progress list."""
    return ProjectProgressResponse(items=get_project_progress_items(db, current_user))


def get_dashboard_summary(
    db: Session,
    current_user: User,
) -> DashboardSummaryResponse:
    """Aggregate real-time KPIs, charts, deadlines, and recent work from SQLite."""
    accessible_ids = get_accessible_project_ids(db, current_user.id)
    today = date.today()
    upcoming_cutoff = today + timedelta(days=7)

    if not accessible_ids:
        return DashboardSummaryResponse(
            total_projects=0,
            active_projects=0,
            completed_projects=0,
            total_stories=0,
            total_tasks=0,
            completed_tasks=0,
            pending_tasks=0,
            overdue_tasks=0,
            tasks_by_status=[StatusCountItem(status=s, count=0) for s in TASK_STATUSES],
            tasks_by_priority=[PriorityCountItem(priority=p, count=0) for p in TASK_PRIORITIES],
            project_progress=[],
            recent_projects=[],
            recent_activity=list_activities(db, current_user, limit=10).items,
            upcoming_deadlines=[],
            overdue_task_list=[],
            recently_updated_tasks=[],
            my_assigned_tasks=[],
        )

    total_projects = len(accessible_ids)
    active_projects = (
        db.scalar(
            select(func.count(Project.id)).where(
                Project.id.in_(accessible_ids),
                Project.status == "Active",
            )
        )
        or 0
    )
    completed_projects = (
        db.scalar(
            select(func.count(Project.id)).where(
                Project.id.in_(accessible_ids),
                Project.status == "Completed",
            )
        )
        or 0
    )
    total_stories = (
        db.scalar(
            select(func.count(UserStory.id)).where(
                UserStory.project_id.in_(accessible_ids)
            )
        )
        or 0
    )

    # Status distribution
    status_rows = db.execute(
        select(Task.status, func.count(Task.id))
        .join(UserStory, Task.user_story_id == UserStory.id)
        .where(UserStory.project_id.in_(accessible_ids))
        .group_by(Task.status)
    ).all()
    status_map = {row[0]: int(row[1]) for row in status_rows}
    tasks_by_status = [
        StatusCountItem(status=s, count=status_map.get(s, 0)) for s in TASK_STATUSES
    ]

    total_tasks = sum(status_map.values())
    completed_tasks = status_map.get("Done", 0)
    pending_tasks = total_tasks - completed_tasks

    # Priority distribution
    priority_rows = db.execute(
        select(Task.priority, func.count(Task.id))
        .join(UserStory, Task.user_story_id == UserStory.id)
        .where(UserStory.project_id.in_(accessible_ids))
        .group_by(Task.priority)
    ).all()
    priority_map = {row[0]: int(row[1]) for row in priority_rows}
    tasks_by_priority = [
        PriorityCountItem(priority=p, count=priority_map.get(p, 0))
        for p in TASK_PRIORITIES
    ]

    overdue_tasks = (
        db.scalar(
            select(func.count(Task.id))
            .join(UserStory, Task.user_story_id == UserStory.id)
            .where(
                UserStory.project_id.in_(accessible_ids),
                Task.status != "Done",
                Task.due_date.is_not(None),
                Task.due_date < today,
            )
        )
        or 0
    )

    # Recent projects
    recent_proj_rows = list(
        db.scalars(
            select(Project)
            .options(joinedload(Project.creator))
            .where(Project.id.in_(accessible_ids))
            .order_by(Project.updated_at.desc(), Project.id.desc())
            .limit(5)
        ).all()
    )
    recent_projects = [
        _serialize_project(db, proj, current_user.id) for proj in recent_proj_rows
    ]

    # Upcoming deadlines (today through +7 days, not Done)
    upcoming_rows = list(
        db.scalars(
            select(Task)
            .join(UserStory, Task.user_story_id == UserStory.id)
            .options(
                joinedload(Task.user_story).joinedload(UserStory.project),
                joinedload(Task.assignee),
            )
            .where(
                UserStory.project_id.in_(accessible_ids),
                Task.status != "Done",
                Task.due_date.is_not(None),
                Task.due_date >= today,
                Task.due_date <= upcoming_cutoff,
            )
            .order_by(Task.due_date.asc(), Task.id.desc())
            .limit(8)
        ).all()
    )

    # Overdue task list
    overdue_rows = list(
        db.scalars(
            select(Task)
            .join(UserStory, Task.user_story_id == UserStory.id)
            .options(
                joinedload(Task.user_story).joinedload(UserStory.project),
                joinedload(Task.assignee),
            )
            .where(
                UserStory.project_id.in_(accessible_ids),
                Task.status != "Done",
                Task.due_date.is_not(None),
                Task.due_date < today,
            )
            .order_by(Task.due_date.asc(), Task.id.desc())
            .limit(8)
        ).all()
    )

    # Recently updated tasks
    recent_task_rows = list(
        db.scalars(
            select(Task)
            .join(UserStory, Task.user_story_id == UserStory.id)
            .options(
                joinedload(Task.user_story).joinedload(UserStory.project),
                joinedload(Task.assignee),
            )
            .where(UserStory.project_id.in_(accessible_ids))
            .order_by(Task.updated_at.desc(), Task.id.desc())
            .limit(6)
        ).all()
    )

    # My assigned tasks
    my_task_rows = list(
        db.scalars(
            select(Task)
            .join(UserStory, Task.user_story_id == UserStory.id)
            .options(
                joinedload(Task.user_story).joinedload(UserStory.project),
                joinedload(Task.assignee),
            )
            .where(
                UserStory.project_id.in_(accessible_ids),
                Task.assignee_id == current_user.id,
            )
            .order_by(Task.due_date.asc().nulls_last(), Task.updated_at.desc())
            .limit(8)
        ).all()
    )

    return DashboardSummaryResponse(
        total_projects=total_projects,
        active_projects=active_projects,
        completed_projects=completed_projects,
        total_stories=total_stories,
        total_tasks=total_tasks,
        completed_tasks=completed_tasks,
        pending_tasks=pending_tasks,
        overdue_tasks=overdue_tasks,
        tasks_by_status=tasks_by_status,
        tasks_by_priority=tasks_by_priority,
        project_progress=get_project_progress_items(db, current_user),
        recent_projects=recent_projects,
        recent_activity=list_activities(db, current_user, limit=10).items,
        upcoming_deadlines=[_serialize_task(t) for t in upcoming_rows],
        overdue_task_list=[_serialize_task(t) for t in overdue_rows],
        recently_updated_tasks=[_serialize_task(t) for t in recent_task_rows],
        my_assigned_tasks=[_serialize_task(t) for t in my_task_rows],
    )
