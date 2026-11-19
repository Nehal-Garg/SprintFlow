"""Phase 7 & 9 background deadline reminder workflow, retry, dedup, and notification tests."""

from datetime import date, timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.background.deadline_reminders import process_task_deadline_reminder
from app.models import BackgroundJobLog, Notification


def _setup_project_and_story(client: TestClient, headers: dict):
    proj = client.post(
        "/projects",
        json={"name": "Deadline Tracker", "status": "Active"},
        headers=headers,
    ).json()
    story = client.post(
        f"/projects/{proj['id']}/stories",
        json={"title": "Async Reminders"},
        headers=headers,
    ).json()
    return proj, story


def test_background_upcoming_deadline_and_assignment_notifications(
    client: TestClient,
    create_auth_user,
    db_session: Session,
):
    """Creating a task due within 2 days triggers both assignment and upcoming_deadline notifications."""
    user, headers = create_auth_user(email="rem_upcoming@sprintflow.dev")
    _, story = _setup_project_and_story(client, headers)

    due_tomorrow = (date.today() + timedelta(days=1)).isoformat()
    res = client.post(
        f"/stories/{story['id']}/tasks",
        json={
            "title": "Finalize API docs",
            "assignee_id": user["id"],
            "due_date": due_tomorrow,
            "priority": "High",
            "status": "In Progress",
        },
        headers=headers,
    )
    assert res.status_code == 201
    task_id = res.json()["id"]

    # FastAPI TestClient executes BackgroundTasks before returning
    notifs_res = client.get("/notifications", headers=headers)
    assert notifs_res.status_code == 200
    body = notifs_res.json()
    types = {item["notification_type"] for item in body["items"]}
    assert "task_assignment" in types
    assert "upcoming_deadline" in types
    assert body["unread_count"] == 2

    # BackgroundJobLog recorded completion
    logs = list(
        db_session.scalars(
            select(BackgroundJobLog).where(BackgroundJobLog.task_id == task_id)
        ).all()
    )
    assert len(logs) >= 1
    assert logs[-1].status == "completed"
    assert logs[-1].attempts == 1


def test_background_overdue_notification_and_duplicate_prevention(
    client: TestClient,
    create_auth_user,
    db_session: Session,
):
    """Overdue tasks generate overdue_task notifications once; repeated updates never duplicate."""
    user, headers = create_auth_user(email="rem_overdue@sprintflow.dev")
    _, story = _setup_project_and_story(client, headers)

    yesterday = (date.today() - timedelta(days=2)).isoformat()
    task = client.post(
        f"/stories/{story['id']}/tasks",
        json={
            "title": "Fix security headers",
            "assignee_id": user["id"],
            "due_date": yesterday,
            "status": "To Do",
        },
        headers=headers,
    ).json()

    # Update task twice without changing due date -> background runs again but prevents duplicates
    assert (
        client.put(
            f"/tasks/{task['id']}",
            json={"description": "Added CORS audit notes"},
            headers=headers,
        ).status_code
        == 200
    )
    assert (
        client.patch(
            f"/tasks/{task['id']}/status",
            json={"status": "In Progress"},
            headers=headers,
        ).status_code
        == 200
    )

    overdue_notifs = list(
        db_session.scalars(
            select(Notification).where(
                Notification.user_id == user["id"],
                Notification.task_id == task["id"],
                Notification.notification_type == "overdue_task",
            )
        ).all()
    )
    assert len(overdue_notifs) == 1

    # Verify duplicate skip was logged
    logs = list(
        db_session.scalars(
            select(BackgroundJobLog)
            .where(BackgroundJobLog.task_id == task["id"])
            .order_by(BackgroundJobLog.id.asc())
        ).all()
    )
    assert logs[0].status == "completed"
    assert any(log.status == "skipped" and "duplicate" in (log.result_summary or "").lower() for log in logs[1:])


def test_completed_task_skips_deadline_reminder(
    client: TestClient,
    create_auth_user,
    db_session: Session,
):
    """Tasks already marked Done must not generate overdue/upcoming deadline notifications."""
    user, headers = create_auth_user(email="rem_done@sprintflow.dev")
    _, story = _setup_project_and_story(client, headers)

    yesterday = (date.today() - timedelta(days=1)).isoformat()
    task = client.post(
        f"/stories/{story['id']}/tasks",
        json={
            "title": "Already shipped task",
            "assignee_id": user["id"],
            "due_date": yesterday,
            "status": "Done",
        },
        headers=headers,
    ).json()

    deadline_notifs = list(
        db_session.scalars(
            select(Notification).where(
                Notification.task_id == task["id"],
                Notification.notification_type.in_(["overdue_task", "upcoming_deadline"]),
            )
        ).all()
    )
    assert len(deadline_notifs) == 0

    log = db_session.scalar(
        select(BackgroundJobLog).where(BackgroundJobLog.task_id == task["id"])
    )
    assert log is not None
    assert log.status == "skipped"


def test_background_bounded_retry_succeeds_after_transient_db_lock(
    client: TestClient,
    create_auth_user,
    session_factory,
    db_session: Session,
):
    """Simulate a transient SQLite OperationalError on attempt 1 and verify retry succeeds on attempt 2."""
    user, headers = create_auth_user(email="rem_retry@sprintflow.dev")
    _, story = _setup_project_and_story(client, headers)

    # Create task outside reminder window first, then manually move due_date to test isolated retry worker
    far_date = (date.today() + timedelta(days=30)).isoformat()
    task = client.post(
        f"/stories/{story['id']}/tasks",
        json={
            "title": "Retryable DB Task",
            "assignee_id": user["id"],
            "due_date": far_date,
        },
        headers=headers,
    ).json()

    # Directly update due_date in DB to tomorrow without firing router background task
    from app.models import Task as TaskModel

    db_task = db_session.get(TaskModel, task["id"])
    db_task.due_date = date.today() + timedelta(days=1)
    db_session.commit()

    call_counter = {"calls": 0}

    def flaky_session_factory():
        call_counter["calls"] += 1
        if call_counter["calls"] == 1:
            raise OperationalError("COMMIT", {}, Exception("database is locked"))
        return session_factory()

    outcome = process_task_deadline_reminder(
        task["id"],
        session_factory=flaky_session_factory,
        max_retries=3,
        base_delay_seconds=0.0,
    )
    assert outcome == "completed"
    assert call_counter["calls"] >= 2

    db_session.expire_all()
    notifs = list(
        db_session.scalars(
            select(Notification).where(
                Notification.task_id == task["id"],
                Notification.notification_type == "upcoming_deadline",
            )
        ).all()
    )
    assert len(notifs) == 1

    latest_log = db_session.scalar(
        select(BackgroundJobLog)
        .where(BackgroundJobLog.task_id == task["id"])
        .order_by(BackgroundJobLog.id.desc())
    )
    assert latest_log is not None
    assert latest_log.status == "completed"
    assert latest_log.attempts == 2


def test_background_exhausted_retries_fails_gracefully_and_logs(
    client: TestClient,
    create_auth_user,
    session_factory,
    db_session: Session,
):
    """When retries are exhausted, the worker never raises and records a failed BackgroundJobLog."""
    user, headers = create_auth_user(email="rem_fail@sprintflow.dev")
    _, story = _setup_project_and_story(client, headers)
    task = client.post(
        f"/stories/{story['id']}/tasks",
        json={"title": "Always Locked Task", "assignee_id": user["id"]},
        headers=headers,
    ).json()

    attempts_seen = {"count": 0}

    def always_locked_then_log_factory():
        attempts_seen["count"] += 1
        # First 3 calls fail with OperationalError; 4th call persists the failure BackgroundJobLog
        if attempts_seen["count"] <= 3:
            raise OperationalError("SELECT", {}, Exception("database is locked"))
        return session_factory()

    outcome = process_task_deadline_reminder(
        task["id"],
        session_factory=always_locked_then_log_factory,
        max_retries=3,
        base_delay_seconds=0.0,
    )
    assert outcome == "failed"

    db_session.expire_all()
    failed_log = db_session.scalar(
        select(BackgroundJobLog)
        .where(
            BackgroundJobLog.task_id == task["id"],
            BackgroundJobLog.status == "failed",
        )
        .order_by(BackgroundJobLog.id.desc())
    )
    assert failed_log is not None
    assert failed_log.attempts == 3
    assert "OperationalError" in (failed_log.error_message or "")


def test_notification_read_read_all_and_ownership_isolation(
    client: TestClient,
    create_auth_user,
):
    """Users can read and mark only their own notifications read; other users receive 403."""
    alice, alice_headers = create_auth_user(email="notif_alice@sprintflow.dev")
    _, bob_headers = create_auth_user(email="notif_bob@sprintflow.dev")
    _, story = _setup_project_and_story(client, alice_headers)

    due_today = date.today().isoformat()
    client.post(
        f"/stories/{story['id']}/tasks",
        json={
            "title": "Submit milestone",
            "assignee_id": alice["id"],
            "due_date": due_today,
        },
        headers=alice_headers,
    )

    alice_notifs = client.get("/notifications", headers=alice_headers).json()
    assert alice_notifs["unread_count"] == 2
    first_id = alice_notifs["items"][0]["id"]

    # Bob sees zero of Alice's notifications and gets 403 when trying to mark hers read
    assert client.get("/notifications", headers=bob_headers).json()["total"] == 0
    assert client.patch(f"/notifications/{first_id}/read", headers=bob_headers).status_code == 403

    # Alice marks one read
    marked = client.patch(f"/notifications/{first_id}/read", headers=alice_headers)
    assert marked.status_code == 200
    assert marked.json()["is_read"] is True
    assert client.get("/notifications", headers=alice_headers).json()["unread_count"] == 1

    # Alice marks all remaining read
    read_all = client.patch("/notifications/read-all", headers=alice_headers)
    assert read_all.status_code == 200
    assert read_all.json()["updated_count"] == 1
    assert client.get("/notifications", headers=alice_headers).json()["unread_count"] == 0

    # Background job logs endpoint returns Alice's project logs and none for Bob
    assert len(client.get("/notifications/job-logs", headers=alice_headers).json()) >= 1
    assert len(client.get("/notifications/job-logs", headers=bob_headers).json()) == 0
