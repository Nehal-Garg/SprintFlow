"""ActivityLog ORM model."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, utcnow

if TYPE_CHECKING:
    from app.models.project import Project
    from app.models.user import User


ACTIVITY_ENTITY_TYPES = ("project", "user_story", "task")


class ActivityLog(Base):
    """Chronological audit trail for project, user story, and task events."""

    __tablename__ = "activity_logs"
    __table_args__ = (
        CheckConstraint(
            "entity_type IN ('project', 'user_story', 'task')",
            name="ck_activity_logs_entity_type",
        ),
        Index("ix_activity_logs_project_created", "project_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    project_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    entity_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True
    )

    # Relationships
    user: Mapped[Optional["User"]] = relationship("User", back_populates="activity_logs")
    project: Mapped[Optional["Project"]] = relationship(
        "Project", back_populates="activity_logs"
    )

    def __repr__(self) -> str:
        return (
            f"<ActivityLog id={self.id} action={self.action!r} "
            f"entity={self.entity_type}:{self.entity_id}>"
        )
