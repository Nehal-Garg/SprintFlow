"""Phase 3 authentication, password hashing, JWT validation, and Swagger tests."""

from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.models import User


def test_register_hashes_password_and_never_exposes_hash(
    client: TestClient,
    db_session: Session,
):
    """Registration creates a bcrypt-hashed password and omits password_hash from response."""
    res = client.post(
        "/auth/register",
        json={
            "full_name": "Priya Nair",
            "email": "Priya.Nair@SprintFlow.Dev",
            "password": "StrongPassword99",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert data["full_name"] == "Priya Nair"
    assert data["email"] == "priya.nair@sprintflow.dev"
    assert "password" not in data
    assert "password_hash" not in data

    # Verify DB stores bcrypt hash, never plain text
    db_user = db_session.scalar(select(User).where(User.email == "priya.nair@sprintflow.dev"))
    assert db_user is not None
    assert db_user.password_hash != "StrongPassword99"
    assert db_user.password_hash.startswith("$2b$")
    assert verify_password("StrongPassword99", db_user.password_hash) is True
    assert verify_password("WrongPassword99", db_user.password_hash) is False


def test_register_rejects_duplicate_email_and_weak_password(client: TestClient):
    """Duplicate emails return 409; weak passwords and invalid emails return 422."""
    # Weak password (no digits)
    weak = client.post(
        "/auth/register",
        json={"full_name": "Weak User", "email": "weak@sprintflow.dev", "password": "onlyletters"},
    )
    assert weak.status_code == 422

    # Invalid email
    bad_email = client.post(
        "/auth/register",
        json={"full_name": "Bad Email", "email": "not-an-email", "password": "Password123"},
    )
    assert bad_email.status_code == 422

    # Valid registration then duplicate email
    first = client.post(
        "/auth/register",
        json={"full_name": "Dev One", "email": "dup@sprintflow.dev", "password": "Password123"},
    )
    assert first.status_code == 201

    second = client.post(
        "/auth/register",
        json={"full_name": "Dev Two", "email": "DUP@sprintflow.dev", "password": "Password123"},
    )
    assert second.status_code == 409


def test_login_and_get_me_flow(client: TestClient):
    """Valid login issues a Bearer JWT that unlocks GET /auth/me without exposing secrets."""
    client.post(
        "/auth/register",
        json={"full_name": "Rohan Verma", "email": "rohan@sprintflow.dev", "password": "Password123"},
    )

    login = client.post(
        "/auth/login",
        json={"email": "rohan@sprintflow.dev", "password": "Password123"},
    )
    assert login.status_code == 200
    body = login.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert "password_hash" not in body["user"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {body['access_token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == "rohan@sprintflow.dev"
    assert "password_hash" not in me.json()


def test_login_invalid_credentials_returns_401(client: TestClient):
    """Wrong password or unknown email returns 401 Unauthorized."""
    client.post(
        "/auth/register",
        json={"full_name": "Ananya Roy", "email": "ananya@sprintflow.dev", "password": "Password123"},
    )

    wrong_pw = client.post(
        "/auth/login",
        json={"email": "ananya@sprintflow.dev", "password": "WrongPassword123"},
    )
    assert wrong_pw.status_code == 401

    unknown_user = client.post(
        "/auth/login",
        json={"email": "ghost@sprintflow.dev", "password": "Password123"},
    )
    assert unknown_user.status_code == 401


def test_protected_endpoints_reject_missing_invalid_and_expired_tokens(
    client: TestClient,
    create_auth_user,
):
    """Protected routes enforce Bearer JWT authentication and reject expired/tampered tokens."""
    user, _ = create_auth_user()

    # Missing token
    assert client.get("/auth/me").status_code == 401
    assert client.get("/projects").status_code == 401
    assert client.get("/my-tasks").status_code == 401

    # Tampered / malformed token
    assert (
        client.get("/auth/me", headers={"Authorization": "Bearer invalid.jwt.token"}).status_code
        == 401
    )

    # Expired token
    expired_token = create_access_token(
        user_id=user["id"],
        email=user["email"],
        expires_delta=timedelta(seconds=-10),
    )
    expired_res = client.get("/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert expired_res.status_code == 401
    assert "expired" in expired_res.json()["detail"].lower()


def test_profile_and_password_update(client: TestClient, create_auth_user):
    """Users can update their profile name and rotate their password."""
    user, headers = create_auth_user(email="me@sprintflow.dev", password="OldPassword1")

    upd = client.put("/auth/me", json={"full_name": "Updated Name"}, headers=headers)
    assert upd.status_code == 200
    assert upd.json()["full_name"] == "Updated Name"

    bad_pw = client.put(
        "/auth/me/password",
        json={"current_password": "WrongOldPassword1", "new_password": "NewPassword2"},
        headers=headers,
    )
    assert bad_pw.status_code == 400

    ok_pw = client.put(
        "/auth/me/password",
        json={"current_password": "OldPassword1", "new_password": "NewPassword2"},
        headers=headers,
    )
    assert ok_pw.status_code == 200

    # Old password fails; new password succeeds
    assert (
        client.post(
            "/auth/login", json={"email": user["email"], "password": "OldPassword1"}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/auth/login", json={"email": user["email"], "password": "NewPassword2"}
        ).status_code
        == 200
    )


def test_swagger_and_openapi_endpoints_available(client: TestClient):
    """Swagger UI (/docs), OpenAPI schema (/openapi.json), and /health are live."""
    assert client.get("/health").status_code == 200

    docs = client.get("/docs")
    assert docs.status_code == 200
    assert "swagger" in docs.text.lower()

    openapi = client.get("/openapi.json")
    assert openapi.status_code == 200
    paths = openapi.json()["paths"]
    for expected_path in (
        "/auth/register",
        "/auth/login",
        "/auth/me",
        "/projects",
        "/projects/{project_id}",
        "/projects/{project_id}/stories",
        "/stories/{story_id}",
        "/stories/{story_id}/tasks",
        "/tasks/{task_id}",
        "/tasks/{task_id}/status",
        "/my-tasks",
    ):
        assert expected_path in paths
