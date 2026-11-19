"""Phase 2 database schema, relationship, integrity, cascade, and constraint tests."""

from datetime import date

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import (
    ActivityLog,
    BackgroundJobLog,
    Notification,
    Project,
    ProjectMember,
    Task,
    User,
    UserStory,
)


def _create_user(db: Session, email: str = "alice@sprintflow.dev", name: str = "Alice Dev") -> User:
    user = User(full_name=name, email=email, password_hash="$2b$12$fakehashedpasswordvalue")
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def _create_hierarchy(db: Session):
    """Helper creating User -> Project -> ProjectMember -> UserStory -> Task."""
    user = _create_user(db)
    project = Project(
        name="E-Commerce Website",
        description="Agile project for storefront MVP",
        start_date=date(2026, 11, 1),
        end_date=date(2026, 12, 31),
        status="Active",
        created_by=user.id,
    )
    db.add(project)
    db.flush()

    member = ProjectMember(project_id=project.id, user_id=user.id, role="owner")
    db.add(member)

    story = UserStory(
        project_id=project.id,
        title="User Authentication",
        description="Allow users to register and log in securely",
        acceptance_criteria="JWT issued on valid login; 401 on invalid credentials",
        priority="High",
        status="In Progress",
        story_points=5,
        assigned_to=user.id,
        due_date=date(2026, 11, 30),
    )
    db.add(story)
    db.flush()

    task = Task(
        user_story_id=story.id,
        title="Develop registration API",
        description="Create POST /auth/register with bcrypt hashing",
        assignee_id=user.id,
        priority="High",
        status="In Progress",
        start_date=date(2026, 11, 15),
        due_date=date(2026, 11, 25),
        estimated_hours=4.0,
        actual_hours=1.5,
    )
    db.add(task)
    db.commit()
    return user, project, member, story, task


def test_init_db_creates_all_expected_tables(db_engine):
    """Verify init_db creates all 7 core tables plus background_job_logs."""
    inspector = inspect(db_engine)
    tables = set(inspector.get_table_names())
    expected = {
        "users",
        "projects",
        "project_members",
        "user_stories",
        "tasks",
        "notifications",
        "activity_logs",
        "background_job_logs",
    }
    assert expected.issubset(tables)


def test_sqlite_foreign_keys_pragma_enabled(db_session: Session):
    """Verify PRAGMA foreign_keys=ON is enforced on every SQLite connection."""
    result = db_session.execute(text("PRAGMA foreign_keys;")).scalar_one()
    assert result == 1


def test_project_story_task_hierarchy_relationships(db_session: Session):
    """Verify full Project -> User Story -> Task ORM relationships in both directions."""
    user, project, member, story, task = _create_hierarchy(db_session)

    loaded_project = db_session.get(Project, project.id)
    assert loaded_project is not None
    assert loaded_project.creator.id == user.id
    assert len(loaded_project.members) == 1
    assert loaded_project.members[0].id == member.id
    assert len(loaded_project.user_stories) == 1

    loaded_story = loaded_project.user_stories[0]
    assert loaded_story.id == story.id
    assert loaded_story.project.id == project.id
    assert loaded_story.assignee.id == user.id
    assert len(loaded_story.tasks) == 1

    loaded_task = loaded_story.tasks[0]
    assert loaded_task.id == task.id
    assert loaded_task.user_story.id == story.id
    assert loaded_task.assignee.id == user.id
    assert loaded_task.estimated_hours == 4.0
    assert loaded_task.actual_hours == 1.5


def test_cannot_create_orphaned_user_story_without_project(db_session: Session):
    """Foreign key enforcement must reject a UserStory referencing a non-existent Project."""
    orphan_story = UserStory(
        project_id=99999,
        title="Orphan Story",
        priority="Medium",
        status="Backlog",
    )
    db_session.add(orphan_story)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_cannot_create_orphaned_task_without_user_story(db_session: Session):
    """Foreign key enforcement must reject a Task referencing a non-existent UserStory."""
    orphan_task = Task(
        user_story_id=99999,
        title="Orphan Task",
        priority="Medium",
        status="To Do",
    )
    db_session.add(orphan_task)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_deleting_story_cascades_to_tasks(db_session: Session):
    """Deleting a UserStory must cascade-delete its child Tasks at the SQLite level."""
    _, _, _, story, task = _create_hierarchy(db_session)
    story_id, task_id = story.id, task.id

    # Use raw SQL DELETE to prove database-level ON DELETE CASCADE works (not just ORM)
    db_session.execute(text("DELETE FROM user_stories WHERE id = :sid"), {"sid": story_id})
    db_session.commit()
    db_session.expunge_all()

    assert db_session.get(UserStory, story_id) is None
    assert db_session.get(Task, task_id) is None


def test_deleting_project_cascades_hierarchy_and_preserves_audit_records(db_session: Session):
    """Deleting a Project cascades to members, stories, and tasks while setting audit FKs to NULL."""
    user, project, member, story, task = _create_hierarchy(db_session)

    notif = Notification(
        user_id=user.id,
        task_id=task.id,
        message="Task deadline approaching",
        notification_type="upcoming_deadline",
        dedup_key=f"upcoming_deadline:task:{task.id}:user:{user.id}:due:2026-11-25",
    )
    activity = ActivityLog(
        user_id=user.id,
        project_id=project.id,
        action="task_created",
        entity_type="task",
        entity_id=task.id,
        description="Created task Develop registration API",
    )
    job_log = BackgroundJobLog(
        job_type="task_deadline_reminder",
        task_id=task.id,
        status="completed",
        attempts=1,
        result_summary="Created upcoming_deadline notification",
    )
    db_session.add_all([notif, activity, job_log])
    db_session.commit()

    user_id, project_id, member_id, story_id, task_id = (
        user.id,
        project.id,
        member.id,
        story.id,
        task.id,
    )
    notif_id, activity_id, job_log_id = notif.id, activity.id, job_log.id

    # Delete project directly via SQL to verify DB-level cascade chain
    db_session.execute(text("DELETE FROM projects WHERE id = :pid"), {"pid": project_id})
    db_session.commit()
    db_session.expunge_all()

    # Cascaded deletions
    assert db_session.get(Project, project_id) is None
    assert db_session.get(ProjectMember, member_id) is None
    assert db_session.get(UserStory, story_id) is None
    assert db_session.get(Task, task_id) is None

    # User & audit records preserved with SET NULL on deleted references
    assert db_session.get(User, user_id) is not None
    persisted_notif = db_session.get(Notification, notif_id)
    persisted_activity = db_session.get(ActivityLog, activity_id)
    persisted_job_log = db_session.get(BackgroundJobLog, job_log_id)

    assert persisted_notif is not None and persisted_notif.task_id is None
    assert persisted_activity is not None and persisted_activity.project_id is None
    assert persisted_job_log is not None and persisted_job_log.task_id is None


def test_orm_delete_project_cascades_cleanly(db_session: Session):
    """Deleting a Project via SQLAlchemy ORM cascades to members, stories, and tasks."""
    _, project, member, story, task = _create_hierarchy(db_session)
    project_id, member_id, story_id, task_id = project.id, member.id, story.id, task.id

    db_session.delete(project)
    db_session.commit()
    db_session.expunge_all()

    assert db_session.get(Project, project_id) is None
    assert db_session.get(ProjectMember, member_id) is None
    assert db_session.get(UserStory, story_id) is None
    assert db_session.get(Task, task_id) is None


def test_unique_constraints_users_and_project_members(db_session: Session):
    """Verify unique email on users and unique (project_id, user_id) on project_members."""
    user, project, _, _, _ = _create_hierarchy(db_session)

    # Duplicate email must fail
    dup_user = User(full_name="Alice Clone", email=user.email, password_hash="hash")
    db_session.add(dup_user)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Duplicate project membership must fail
    dup_member = ProjectMember(project_id=project.id, user_id=user.id, role="member")
    db_session.add(dup_member)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_notification_deduplication_unique_constraint(db_session: Session):
    """Verify (user_id, dedup_key) prevents duplicate notifications per user."""
    user1, _, _, _, task = _create_hierarchy(db_session)
    user2 = _create_user(db_session, email="bob@sprintflow.dev", name="Bob Dev")

    dedup_key = f"overdue_task:task:{task.id}:due:2026-11-25"

    n1 = Notification(
        user_id=user1.id,
        task_id=task.id,
        message="Task is overdue",
        notification_type="overdue_task",
        dedup_key=dedup_key,
    )
    db_session.add(n1)
    db_session.commit()

    # Exact duplicate for same user must be rejected by DB constraint
    n1_dup = Notification(
        user_id=user1.id,
        task_id=task.id,
        message="Task is overdue (retry duplicate)",
        notification_type="overdue_task",
        dedup_key=dedup_key,
    )
    db_session.add(n1_dup)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Same dedup_key for a different user is allowed
    n2 = Notification(
        user_id=user2.id,
        task_id=task.id,
        message="Task is overdue",
        notification_type="overdue_task",
        dedup_key=dedup_key,
    )
    # Different dedup_key for the same user is allowed
    n3 = Notification(
        user_id=user1.id,
        task_id=task.id,
        message="Task was assigned to you",
        notification_type="task_assignment",
        dedup_key=f"task_assignment:task:{task.id}:user:{user1.id}:v1",
    )
    db_session.add_all([n2, n3])
    db_session.commit()

    assert n2.id is not None
    assert n3.id is not None


def test_check_constraints_enforce_valid_enums_and_non_negative_values(db_session: Session):
    """Verify SQLite CHECK constraints block invalid statuses, priorities, and negative numbers."""
    user, project, _, story, _ = _create_hierarchy(db_session)

    # Invalid project status
    db_session.add(Project(name="Bad Proj", status="Archived", created_by=user.id))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Negative story points
    db_session.add(
        UserStory(project_id=project.id, title="Bad Story", story_points=-3)
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Invalid task status
    db_session.add(
        Task(user_story_id=story.id, title="Bad Task", status="Blocked")
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Negative estimated hours
    db_session.add(
        Task(user_story_id=story.id, title="Negative Hours", estimated_hours=-2.5)
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Invalid notification type
    db_session.add(
        Notification(
            user_id=user.id,
            message="Invalid type",
            notification_type="marketing_promo",
            dedup_key="promo:1",
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()

    # Invalid background job log status
    db_session.add(
        BackgroundJobLog(job_type="task_deadline_reminder", status="unknown", attempts=1)
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_background_job_logs_attempt_tracking_and_failure_recording(db_session: Session):
    """Verify background_job_logs stores completed, skipped, and failed attempts accurately."""
    _, _, _, _, task = _create_hierarchy(db_session)

    log_failed = BackgroundJobLog(
        job_type="task_deadline_reminder",
        task_id=task.id,
        status="failed",
        attempts=3,
        result_summary="Exhausted bounded retries",
        error_message="OperationalError: database is locked",
    )
    log_skipped = BackgroundJobLog(
        job_type="task_deadline_reminder",
        task_id=task.id,
        status="skipped",
        attempts=1,
        result_summary="Duplicate reminder already exists",
    )
    db_session.add_all([log_failed, log_skipped])
    db_session.commit()

    loaded_failed = db_session.get(BackgroundJobLog, log_failed.id)
    loaded_skipped = db_session.get(BackgroundJobLog, log_skipped.id)

    assert loaded_failed is not None
    assert loaded_failed.status == "failed"
    assert loaded_failed.attempts == 3
    assert "database is locked" in (loaded_failed.error_message or "")

    assert loaded_skipped is not None
    assert loaded_skipped.status == "skipped"
    assert loaded_skipped.attempts == 1
    assert loaded_skipped.error_message is None


def test_schema_contains_expected_foreign_keys_and_indexes(db_engine):
    """Inspect SQLite metadata to verify critical FKs and indexes are registered."""
    inspector = inspect(db_engine)

    story_fks = {fk["referred_table"] for fk in inspector.get_foreign_keys("user_stories")}
    assert {"projects", "users"}.issubset(story_fks)

    task_fks = {fk["referred_table"] for fk in inspector.get_foreign_keys("tasks")}
    assert {"user_stories", "users"}.issubset(task_fks)

    notif_uniques = {
        tuple(u["column_names"]) for u in inspector.get_unique_constraints("notifications")
    }
    assert ("user_id", "dedup_key") in notif_uniques

    task_indexes = {idx["name"] for idx in inspector.get_indexes("tasks")}
    assert "ix_tasks_story_status" in task_indexes
    assert "ix_tasks_assignee_status" in task_indexes
