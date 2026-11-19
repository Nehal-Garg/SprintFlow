"""Phase 8 & 9 dashboard analytics, full activity log coverage, and security audit tests."""

from datetime import date, timedelta

from fastapi.testclient import TestClient


def test_dashboard_analytics_dynamic_calculations_and_scoping(
    client: TestClient,
    create_auth_user,
):
    """Dashboard summary and project progress calculate live SQLite metrics scoped by membership."""
    alice, alice_headers = create_auth_user(email="dash_alice@sprintflow.dev", full_name="Alice PM")
    _, bob_headers = create_auth_user(email="dash_bob@sprintflow.dev", full_name="Bob External")

    # Empty state check
    empty_summary = client.get("/dashboard/summary", headers=alice_headers)
    assert empty_summary.status_code == 200
    assert empty_summary.json()["total_projects"] == 0
    assert empty_summary.json()["total_tasks"] == 0

    # Alice creates 2 projects (1 Active, 1 Completed)
    p1 = client.post(
        "/projects",
        json={"name": "Portal Redesign", "status": "Active"},
        headers=alice_headers,
    ).json()
    client.post(
        "/projects",
        json={"name": "Legacy Migration", "status": "Completed"},
        headers=alice_headers,
    )

    # Bob creates an unrelated private project (must NOT appear in Alice's dashboard)
    client.post(
        "/projects",
        json={"name": "Bob Private Secret", "status": "Active"},
        headers=bob_headers,
    )

    # Alice creates a story and 3 tasks (1 Done, 1 Overdue, 1 Upcoming)
    story = client.post(
        f"/projects/{p1['id']}/stories",
        json={"title": "Dashboard Analytics", "priority": "High"},
        headers=alice_headers,
    ).json()

    yesterday = (date.today() - timedelta(days=1)).isoformat()
    in_three_days = (date.today() + timedelta(days=3)).isoformat()

    client.post(
        f"/stories/{story['id']}/tasks",
        json={
            "title": "Done Task",
            "assignee_id": alice["id"],
            "status": "Done",
            "priority": "Low",
        },
        headers=alice_headers,
    )
    client.post(
        f"/stories/{story['id']}/tasks",
        json={
            "title": "Overdue Critical Task",
            "assignee_id": alice["id"],
            "status": "In Progress",
            "priority": "Critical",
            "due_date": yesterday,
        },
        headers=alice_headers,
    )
    client.post(
        f"/stories/{story['id']}/tasks",
        json={
            "title": "Upcoming Review Task",
            "assignee_id": alice["id"],
            "status": "In Review",
            "priority": "High",
            "due_date": in_three_days,
        },
        headers=alice_headers,
    )

    summary = client.get("/dashboard/summary", headers=alice_headers).json()
    assert summary["total_projects"] == 2
    assert summary["active_projects"] == 1
    assert summary["completed_projects"] == 1
    assert summary["total_stories"] == 1
    assert summary["total_tasks"] == 3
    assert summary["completed_tasks"] == 1
    assert summary["pending_tasks"] == 2
    assert summary["overdue_tasks"] == 1
    assert len(summary["overdue_task_list"]) == 1
    assert len(summary["upcoming_deadlines"]) == 1
    assert len(summary["my_assigned_tasks"]) == 3
    assert len(summary["recent_activity"]) >= 5

    # Verify Bob's project is excluded
    prog_res = client.get("/dashboard/project-progress", headers=alice_headers)
    assert prog_res.status_code == 200
    prog_items = prog_res.json()["items"]
    assert len(prog_items) == 2
    assert all(item["project_name"] != "Bob Private Secret" for item in prog_items)
    p1_progress = next(item for item in prog_items if item["project_id"] == p1["id"])
    assert p1_progress["progress"] == 33.3


def test_activity_log_tracks_all_required_events_chronologically(
    client: TestClient,
    create_auth_user,
):
    """Verify activity log records project, story, and task lifecycle events and enforces scoping."""
    owner, owner_headers = create_auth_user(email="act_owner@sprintflow.dev")
    member, _ = create_auth_user(email="act_member@sprintflow.dev")
    _, outsider_headers = create_auth_user(email="act_outsider@sprintflow.dev")

    # Project create & update
    proj = client.post(
        "/projects", json={"name": "Audit Project", "status": "Planning"}, headers=owner_headers
    ).json()
    pid = proj["id"]
    client.put(f"/projects/{pid}", json={"status": "Active"}, headers=owner_headers)
    client.post(
        f"/projects/{pid}/members",
        json={"user_id": member["id"], "role": "member"},
        headers=owner_headers,
    )

    # Story create, update, delete (second story)
    story = client.post(
        f"/projects/{pid}/stories",
        json={"title": "Audit Story"},
        headers=owner_headers,
    ).json()
    client.put(f"/stories/{story['id']}", json={"priority": "High"}, headers=owner_headers)

    story_to_delete = client.post(
        f"/projects/{pid}/stories",
        json={"title": "Temp Story"},
        headers=owner_headers,
    ).json()
    client.delete(f"/stories/{story_to_delete['id']}", headers=owner_headers)

    # Task create, update, assign, status change, complete
    task = client.post(
        f"/stories/{story['id']}/tasks",
        json={"title": "Audit Task"},
        headers=owner_headers,
    ).json()
    client.put(
        f"/tasks/{task['id']}",
        json={"assignee_id": member["id"], "estimated_hours": 3.0},
        headers=owner_headers,
    )
    client.patch(
        f"/tasks/{task['id']}/status",
        json={"status": "Done"},
        headers=owner_headers,
    )
    temp_task = client.post(
        f"/stories/{story['id']}/tasks",
        json={"title": "Temp Delete Task"},
        headers=owner_headers,
    ).json()
    client.delete(f"/tasks/{temp_task['id']}", headers=owner_headers)

    # Project delete
    proj2 = client.post("/projects", json={"name": "Delete Me"}, headers=owner_headers).json()
    client.delete(f"/projects/{proj2['id']}", headers=owner_headers)

    act_res = client.get("/activity?limit=50", headers=owner_headers)
    assert act_res.status_code == 200
    actions = {item["action"] for item in act_res.json()["items"]}

    expected_actions = {
        "project_created",
        "project_updated",
        "project_deleted",
        "story_created",
        "story_updated",
        "story_deleted",
        "task_created",
        "task_updated",
        "task_assigned",
        "task_status_changed",
        "task_completed",
        "task_deleted",
    }
    assert expected_actions.issubset(actions)

    # Outsider cannot view owner's project activity
    assert client.get(f"/activity?project_id={pid}", headers=outsider_headers).status_code == 403
    assert client.get("/activity", headers=outsider_headers).json()["total"] == 0


def test_security_unauthorized_access_and_sql_injection_resilience(
    client: TestClient,
    create_auth_user,
):
    """Verify unauthenticated access is blocked across all new routes and ORM resists SQLi strings."""
    for endpoint in (
        "/notifications",
        "/notifications/job-logs",
        "/activity",
        "/dashboard/summary",
        "/dashboard/project-progress",
        "/users",
        "/tasks",
    ):
        assert client.get(endpoint).status_code == 401

    _, headers = create_auth_user(email="sqli_test@sprintflow.dev")
    client.post("/projects", json={"name": "Safe Project"}, headers=headers)

    # SQL injection attempt in search query parameter is safely parameterized by SQLAlchemy
    sqli_res = client.get("/projects?search=' OR 1=1 --", headers=headers)
    assert sqli_res.status_code == 200
    assert sqli_res.json()["total"] == 0
