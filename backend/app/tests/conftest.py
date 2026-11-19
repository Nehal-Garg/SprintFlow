"""Shared Pytest fixtures for isolated SQLite database and FastAPI TestClient."""

from pathlib import Path
from typing import Callable, Dict, Tuple

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.core.dependencies import get_db, get_session_factory
from app.database import create_db_engine, init_db
from app.main import create_app


@pytest.fixture()
def db_engine(tmp_path: Path):
    """Create a fresh, isolated file-backed SQLite database per test."""
    db_file = tmp_path / "test_sprintflow.db"
    engine = create_db_engine(f"sqlite:///{db_file.as_posix()}")
    init_db(engine)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture()
def session_factory(db_engine):
    """Return a sessionmaker bound to the isolated test engine."""
    return sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine,
        expire_on_commit=False,
    )


@pytest.fixture()
def db_session(session_factory) -> Session:
    """Provide a SQLAlchemy Session bound to the isolated test database."""
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def client(session_factory):
    """Provide a FastAPI TestClient wired to the isolated SQLite test database."""
    app = create_app()

    def _override_get_db():
        db = session_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_session_factory] = lambda: session_factory
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture()
def create_auth_user(client: TestClient) -> Callable[..., Tuple[dict, Dict[str, str]]]:
    """Helper fixture that registers and logs in a user, returning (user_dict, auth_headers)."""

    def _factory(
        email: str = "alice@sprintflow.dev",
        full_name: str = "Alice Engineer",
        password: str = "SecurePass123",
    ) -> Tuple[dict, Dict[str, str]]:
        reg = client.post(
            "/auth/register",
            json={"full_name": full_name, "email": email, "password": password},
        )
        assert reg.status_code == 201, reg.text
        login = client.post(
            "/auth/login",
            json={"email": email, "password": password},
        )
        assert login.status_code == 200, login.text
        token = login.json()["access_token"]
        return reg.json(), {"Authorization": f"Bearer {token}"}

    return _factory
