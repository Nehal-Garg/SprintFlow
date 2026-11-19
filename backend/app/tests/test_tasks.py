"""Phase 3 Task CRUD, status transition, hierarchy, and authorization tests."""

from datetime import date, timedelta

from fastapi.testclient import TestClient


def test_full_hierarchy_project_story_task_and_status_updates(
    client: TestClient,
    create_auth_user,
):
    """Verify Project -> User Story -> Task creation, status patch, progress, and cascade delete."""
    owner, owner_headers = create_auth_user(email="arch@sprintflow.dev", full_name="Lead Architect")
    dev, dev_headers = create_auth_user(email="dev2@sprintflow.dev", full_name="Backend Dev")

    # 1. Create project & add dev as member
    proj = client.post(
        "/projects", json={"name": "E-Commerce Website", "status": "Active"}, headers=owner_headers
    ).json()
    pid = proj["id"]
    client.post(
        f"/projects/{pid}/members",
        json={"user_id": dev["id"], "role": "member"},
        headers=owner_headers,
    )

    # 2. Create user story
    story = client.post(
        f"/projects/{pid}/stories",
        json={"title": "User Authentication", "priority": "High"},
        headers=owner_headers,
    ).json()
    sid = story["id"]

    # 3. Create 2 tasks under story
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    next_week = (date.today() + timedelta(days=7)).isoformat()

    t1_res = client.post(
        f"/stories/{sid}/tasks",
        json={
            "title": "Design login interface",
            "description": "Black/green/white login view",
            "assignee_id": dev["id"],
            "priority": "High",
            "status": "To Do",
            "due_date": yesterday,
            "estimated_hours": 3.0,
        },
        headers=owner_headers,
    )
    assert t1_res.status_code == 201
    t1 = t1_res.json()
    assert t1["project_id"] == pid
    assert t1["user_story_id"] == sid
    assert t1["is_overdue"] is True

    t2_res = client.post(
        f"/stories/{sid}/tasks",
        json={
            "title": "Develop registration API",
            "assignee_id": owner["id"],
            "priority": "Medium",
            "status": "In Progress",
            "due_date": next_week,
            "estimated_hours": 5.0,
            "actual_hours": 2.0,
        },
        headers=owner_headers,
    )
    assert t2_res.status_code == 201
    t2 = t2_res.json()
    assert t2["is_overdue"] is False

    # 4. PATCH task status to Done and verify project progress recalculates to 50.0%
    patch_res = client.patch(
        f"/tasks/{t1['id']}/status",
        json={"status": "Done"},
        headers=dev_headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "Done"
    assert patch_res.json()["is_overdue"] is False

    refreshed_project = client.get(f"/projects/{pid}", headers=owner_headers).json()
    assert refreshed_project["story_count"] == 1
    assert refreshed_project["task_count"] == 2
    assert refreshed_project["completed_task_count"] == 1
    assert refreshed_project["progress"] == 50.0

    # 5. PUT full task update
    upd = client.put(
        f"/tasks/{t2['id']}",
        json={"actual_hours": 4.5, "priority": "Critical"},
        headers=owner_headers,
    )
    assert upd.status_code == 200
    assert upd.json()["actual_hours"] == 4.5
    assert upd.json()["priority"] == "Critical"

    # 6. GET /my-tasks strictly isolates each user's assigned tasks
    dev_my_tasks = client.get("/my-tasks", headers=dev_headers).json()
    assert dev_my_tasks["total"] == 1
    assert dev_my_tasks["items"][0]["id"] == t1["id"]

    owner_my_tasks = client.get("/my-tasks", headers=owner_headers).json()
    assert owner_my_tasks["total"] == 1
    assert owner_my_tasks["items"][0]["id"] == t2["id"]

    # 7. Delete task
    assert client.delete(f"/tasks/{t2['id']}", headers=owner_headers).status_code == 204
    assert client.get(f"/tasks/{t2['id']}", headers=owner_headers).status_code == 404

    # 8. Deleting project cascades remaining story and task cleanly
    assert client.delete(f"/projects/{pid}", headers=owner_headers).status_code == 204
    assert client.get(f"/stories/{sid}", headers=owner_headers).status_code == 404
    assert client.get(f"/tasks/{t1['id']}", headers=owner_headers).status_code == 404


def test_task_authorization_invalid_fk_and_tampering(client: TestClient, create_auth_user):
    """Block invalid story FK, non-member assignment, outsider access, and user_story_id tampering."""
    _, owner_headers = create_auth_user(email="t_owner@sprintflow.dev")
    outsider, outsider_headers = create_auth_user(email="t_outsider@sprintflow.dev")

    # Non-existent user story returns 404
    assert (
        client.post(
            "/stories/99999/tasks",
            json={"title": "Orphan API Task"},
            headers=owner_headers,
        ).status_code
        == 404
    )

    proj = client.post("/projects", json={"name": "Task Auth Proj"}, headers=owner_headers).json()
    story = client.post(
        f"/projects/{proj['id']}/stories",
        json={"title": "Auth Story"},
        headers=owner_headers,
    ).json()

    # Cannot assign task to non-member
    bad_assign = client.post(
        f"/stories/{story['id']}/tasks",
        json={"title": "Bad Assign", "assignee_id": outsider["id"]},
        headers=owner_headers,
    )
    assert bad_assign.status_code == 400

    # Invalid status value rejected (422)
    bad_status = client.post(
        f"/stories/{story['id']}/tasks",
        json={"title": "Bad Status", "status": "Archived"},
        headers=owner_headers,
    )
    assert bad_status.status_code == 422

    # Valid task
    task = client.post(
        f"/stories/{story['id']}/tasks",
        json={"title": "Valid Task"},
        headers=owner_headers,
    ).json()

    # Outsider cannot read, update, patch status, or delete
    assert client.get(f"/tasks/{task['id']}", headers=outsider_headers).status_code == 403
    assert (
        client.put(
            f"/tasks/{task['id']}", json={"title": "Hacked"}, headers=outsider_headers
        ).status_code
        == 403
    )
    assert (
        client.patch(
            f"/tasks/{task['id']}/status", json={"status": "Done"}, headers=outsider_headers
        ).status_code
        == 403
    )
    assert client.delete(f"/tasks/{task['id']}", headers=outsider_headers).status_code == 403

    # Cannot tamper with user_story_id or id on update
    tamper = client.put(
        f"/tasks/{task['id']}",
        json={"title": "Tampered", "user_story_id": 999},
        headers=owner_headers,
    )
    assert tamper.status_code == 422
