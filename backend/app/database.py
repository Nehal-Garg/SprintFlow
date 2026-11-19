"""SQLAlchemy database setup, SQLite foreign key enforcement, and schema initialization."""

import sqlite3
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import get_settings


def utcnow() -> datetime:
    """Return a timezone-aware UTC timestamp."""
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    """Declarative base for all SprintFlow SQLAlchemy ORM models."""


@event.listens_for(Engine, "connect")
def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    """Enforce SQLite referential integrity (PRAGMA foreign_keys=ON) on every connection."""
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()


def create_db_engine(database_url: Optional[str] = None) -> Engine:
    """Create a configured SQLAlchemy engine for the target database URL."""
    url = database_url or get_settings().database_url
    connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(
        url,
        connect_args=connect_args,
        future=True,
    )


engine = create_db_engine()
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


def init_db(target_engine: Optional[Engine] = None) -> None:
    """Import all ORM models and create all database tables if they do not exist."""
    import app.models  # noqa: F401 - ensures all models are registered on Base.metadata

    Base.metadata.create_all(bind=target_engine or engine)
