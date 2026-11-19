"""Phase 3 project CRUD, membership, and authorization tests."""

from fastapi.testclient import TestClient


def test_project_crud_search_filter_and_progress(client: TestClient, create_auth_user):
    """Owners can create, list, search, filter, update, and delete projects."""
    owner, headers = create_auth_user(email="owner@sprintflow.dev", full_name="Owner User")

    # Create
    create_res = client.post(
        "/projects",
        json={
            "name": "E-Commerce Website",
            "description": "Online retail storefront",
            "start_date": "2026-11-01",
            "end_date": "2026-12-20",
            "status": "Active",
        },
        headers=headers,
    )
    assert create_res.status_code == 201
    project = create_res.json()
    assert project["name"] == "E-Commerce Website"
    assert project["created_by"] == owner["id"]
    assert project["current_user_role"] == "owner"
    assert project["progress"] == 0.0
    assert len(project["members"]) == 1

    # Second project for filtering
    client.post(
        "/projects",
        json={"name": "Internal CLI", "status": "Planning"},
        headers=headers,
    )

    # Search & status filter
    active_list = client.get("/projects?status=Active", headers=headers)
    assert active_list.status_code == 200
    assert active_list.json()["total"] == 1
    assert active_list.json()["items"][0]["id"] == project["id"]

    search_list = client.get("/projects?search=storefront", headers=headers)
    assert search_list.status_code == 200
    assert search_list.json()["total"] == 1

    # Read detail
    detail = client.get(f"/projects/{project['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["name"] == "E-Commerce Website"

    # Update
    update = client.put(
        f"/projects/{project['id']}",
        json={"name": "E-Commerce Platform", "status": "On Hold"},
        headers=headers,
    )
    assert update.status_code == 200
    assert update.json()["name"] == "E-Commerce Platform"
    assert update.json()["status"] == "On Hold"

    # Delete
    deleted = client.delete(f"/projects/{project['id']}", headers=headers)
    assert deleted.status_code == 204
    assert client.get(f"/projects/{project['id']}", headers=headers).status_code == 404


def test_project_authorization_owner_vs_member_vs_outsider(client: TestClient, create_auth_user):
    """Enforce strict owner, member, and non-member authorization boundaries."""
    owner, owner_headers = create_auth_user(email="lead@sprintflow.dev", full_name="Team Lead")
    member, member_headers = create_auth_user(email="dev@sprintflow.dev", full_name="Team Dev")
    outsider, outsider_headers = create_auth_user(
        email="outsider@sprintflow.dev", full_name="External User"
    )

    proj = client.post(
        "/projects",
        json={"name": "Private Roadmap", "status": "Active"},
        headers=owner_headers,
    ).json()
    pid = proj["id"]

    # Outsider cannot see project in list, read, update, delete, or add members
    assert client.get("/projects", headers=outsider_headers).json()["total"] == 0
    assert client.get(f"/projects/{pid}", headers=outsider_headers).status_code == 403
    assert (
        client.put(f"/projects/{pid}", json={"name": "Hacked"}, headers=outsider_headers).status_code
        == 403
    )
    assert client.delete(f"/projects/{pid}", headers=outsider_headers).status_code == 403

    # Owner adds member
    add_res = client.post(
        f"/projects/{pid}/members",
        json={"user_id": member["id"], "role": "member"},
        headers=owner_headers,
    )
    assert add_res.status_code == 201
    assert add_res.json()["role"] == "member"

    # Member can view and edit project details
    assert client.get(f"/projects/{pid}", headers=member_headers).status_code == 200
    assert (
        client.put(
            f"/projects/{pid}",
            json={"description": "Updated by member"},
            headers=member_headers,
        ).status_code
        == 200
    )

    # Member CANNOT delete the project or manage membership (owner-only actions)
    assert client.delete(f"/projects/{pid}", headers=member_headers).status_code == 403
    assert (
        client.post(
            f"/projects/{pid}/members",
            json={"user_id": outsider["id"], "role": "member"},
            headers=member_headers,
        ).status_code
        == 403
    )

    # Owner cannot remove the sole owner
    assert (
        client.delete(f"/projects/{pid}/members/{owner['id']}", headers=owner_headers).status_code
        == 400
    )

    # Owner removes member -> member loses access immediately
    assert (
        client.delete(f"/projects/{pid}/members/{member['id']}", headers=owner_headers).status_code
        == 204
    )
    assert client.get(f"/projects/{pid}", headers=member_headers).status_code == 403


def test_project_rejects_invalid_dates_and_ownership_tampering(client: TestClient, create_auth_user):
    """Reject end_date < start_date and forbid extra fields like id/created_by."""
    _, headers = create_auth_user(email="sec@sprintflow.dev")

    # end_date before start_date
    bad_dates = client.post(
        "/projects",
        json={"name": "Time Travel", "start_date": "2026-12-10", "end_date": "2026-12-01"},
        headers=headers,
    )
    assert bad_dates.status_code == 422

    # Attempt to inject created_by or id (mass assignment prevention)
    tamper_create = client.post(
        "/projects",
        json={"name": "Injected Owner", "created_by": 999},
        headers=headers,
    )
    assert tamper_create.status_code == 422

    proj = client.post("/projects", json={"name": "Clean Project"}, headers=headers).json()
    tamper_update = client.put(
        f"/projects/{proj['id']}",
        json={"name": "Updated", "created_by": 999},
        headers=headers,
    )
    assert tamper_update.status_code == 422
