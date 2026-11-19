"""Phase 3 User Story CRUD, filtering, and authorization tests."""

from fastapi.testclient import TestClient


def test_story_crud_and_filtering(client: TestClient, create_auth_user):
    """Create, read, filter, update, and delete user stories under an authorized project."""
    owner, headers = create_auth_user(email="pm@sprintflow.dev")
    project = client.post(
        "/projects", json={"name": "SprintFlow Core"}, headers=headers
    ).json()
    pid = project["id"]

    # Create stories
    s1 = client.post(
        f"/projects/{pid}/stories",
        json={
            "title": "User Authentication",
            "description": "JWT login and registration",
            "acceptance_criteria": "Returns 201 on register, 200 + token on login",
            "priority": "Critical",
            "status": "In Progress",
            "story_points": 8,
            "assigned_to": owner["id"],
            "due_date": "2026-12-01",
        },
        headers=headers,
    )
    assert s1.status_code == 201
    story1 = s1.json()
    assert story1["project_id"] == pid
    assert story1["assignee_name"] == owner["full_name"]

    s2 = client.post(
        f"/projects/{pid}/stories",
        json={"title": "Product Search", "priority": "Low", "status": "Backlog"},
        headers=headers,
    )
    assert s2.status_code == 201

    # Filter by priority & status
    crit = client.get(f"/projects/{pid}/stories?priority=Critical", headers=headers)
    assert crit.status_code == 200
    assert crit.json()["total"] == 1
    assert crit.json()["items"][0]["id"] == story1["id"]

    backlog = client.get(f"/projects/{pid}/stories?status=Backlog", headers=headers)
    assert backlog.status_code == 200
    assert backlog.json()["total"] == 1

    # Read direct
    get_res = client.get(f"/stories/{story1['id']}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "User Authentication"

    # Update
    upd = client.put(
        f"/stories/{story1['id']}",
        json={"status": "Done", "story_points": 5},
        headers=headers,
    )
    assert upd.status_code == 200
    assert upd.json()["status"] == "Done"
    assert upd.json()["story_points"] == 5

    # Delete
    assert client.delete(f"/stories/{story1['id']}", headers=headers).status_code == 204
    assert client.get(f"/stories/{story1['id']}", headers=headers).status_code == 404


def test_story_validation_and_authorization_rules(client: TestClient, create_auth_user):
    """Enforce project existence, project membership, assignee membership, and immutable project_id."""
    _, owner_headers = create_auth_user(email="story_owner@sprintflow.dev")
    outsider, outsider_headers = create_auth_user(email="story_outsider@sprintflow.dev")

    project = client.post(
        "/projects", json={"name": "Secure App"}, headers=owner_headers
    ).json()
    pid = project["id"]

    # Non-existent project returns 404
    assert (
        client.post(
            "/projects/99999/stories",
            json={"title": "Ghost Story"},
            headers=owner_headers,
        ).status_code
        == 404
    )

    # Cannot assign story to a user who is not a project member
    bad_assignee = client.post(
        f"/projects/{pid}/stories",
        json={"title": "Auth Story", "assigned_to": outsider["id"]},
        headers=owner_headers,
    )
    assert bad_assignee.status_code == 400

    # Outsider cannot create or read stories in another user's project
    assert (
        client.post(
            f"/projects/{pid}/stories",
            json={"title": "Unauthorized Story"},
            headers=outsider_headers,
        ).status_code
        == 403
    )

    story = client.post(
        f"/projects/{pid}/stories",
        json={"title": "Valid Story"},
        headers=owner_headers,
    ).json()

    assert client.get(f"/stories/{story['id']}", headers=outsider_headers).status_code == 403
    assert (
        client.put(
            f"/stories/{story['id']}", json={"title": "Hijacked"}, headers=outsider_headers
        ).status_code
        == 403
    )
    assert client.delete(f"/stories/{story['id']}", headers=outsider_headers).status_code == 403

    # Cannot tamper with project_id on update
    tamper = client.put(
        f"/stories/{story['id']}",
        json={"title": "Moved", "project_id": 999},
        headers=owner_headers,
    )
    assert tamper.status_code == 422
