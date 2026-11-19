"""Task ORM model."""

from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, utcnow

if TYPE_CHECKING:
    from app.models.background_job_log import BackgroundJobLog
    from app.models.notification import Notification
    from app.models.user import User
    from app.models.user_story import UserStory


TASK_PRIORITIES = ("Low", "Medium", "High", "Critical")
TASK_STATUSES = ("To Do", "In Progress", "In Review", "Done")


class Task(Base):
    """Third-level Agile work item belonging strictly to a UserStory."""

    __tablename__ = "tasks"
    __table_args__ = (
        CheckConstraint(
            "priority IN ('Low', 'Medium', 'High', 'Critical')",
            name="ck_tasks_priority",
        ),
        CheckConstraint(
            "status IN ('To Do', 'In Progress', 'In Review', 'Done')",
            name="ck_tasks_status",
        ),
        CheckConstraint(
            "estimated_hours IS NULL OR estimated_hours >= 0",
            name="ck_tasks_estimated_hours_non_negative",
        ),
        CheckConstraint(
            "actual_hours IS NULL OR actual_hours >= 0",
            name="ck_tasks_actual_hours_non_negative",
        ),
        Index("ix_tasks_story_status", "user_story_id", "status"),
        Index("ix_tasks_assignee_status", "assignee_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_story_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("user_stories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assignee_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    priority: Mapped[str] = mapped_column(
        String(20), nullable=False, default="Medium", index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="To Do", index=True
    )
    start_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    estimated_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    actual_hours: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    # Relationships
    user_story: Mapped["UserStory"] = relationship("UserStory", back_populates="tasks")
    assignee: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="assigned_tasks",
        foreign_keys=[assignee_id],
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        back_populates="task",
        passive_deletes=True,
    )
    background_job_logs: Mapped[List["BackgroundJobLog"]] = relationship(
        "BackgroundJobLog",
        back_populates="task",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return (
            f"<Task id={self.id} user_story_id={self.user_story_id} "
            f"title={self.title!r} status={self.status!r}>"
        )
