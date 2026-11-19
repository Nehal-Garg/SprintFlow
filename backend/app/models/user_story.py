"""UserStory ORM model."""

from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    CheckConstraint,
    Date,
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
    from app.models.task import Task
    from app.models.user import User


STORY_PRIORITIES = ("Low", "Medium", "High", "Critical")
STORY_STATUSES = ("Backlog", "To Do", "In Progress", "Done")


class UserStory(Base):
    """Second-level Agile work item belonging strictly to a Project."""

    __tablename__ = "user_stories"
    __table_args__ = (
        CheckConstraint(
            "priority IN ('Low', 'Medium', 'High', 'Critical')",
            name="ck_user_stories_priority",
        ),
        CheckConstraint(
            "status IN ('Backlog', 'To Do', 'In Progress', 'Done')",
            name="ck_user_stories_status",
        ),
        CheckConstraint(
            "story_points IS NULL OR story_points >= 0",
            name="ck_user_stories_story_points_non_negative",
        ),
        Index("ix_user_stories_project_status", "project_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    acceptance_criteria: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Medium", index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Backlog", index=True
    )
    story_points: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    assigned_to: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="user_stories")
    assignee: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="assigned_stories",
        foreign_keys=[assigned_to],
    )
    tasks: Mapped[List["Task"]] = relationship(
        "Task",
        back_populates="user_story",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return (
            f"<UserStory id={self.id} project_id={self.project_id} "
            f"title={self.title!r} status={self.status!r}>"
        )
