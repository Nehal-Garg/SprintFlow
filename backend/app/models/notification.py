"""Notification ORM model."""

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, utcnow

if TYPE_CHECKING:
    from app.models.task import Task
    from app.models.user import User


NOTIFICATION_TYPES = ("upcoming_deadline", "overdue_task", "task_assignment")


class Notification(Base):
    """Persistent user notification with database-enforced deduplication."""

    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "dedup_key",
            name="uq_notifications_user_dedup_key",
        ),
        CheckConstraint(
            "notification_type IN ('upcoming_deadline', 'overdue_task', 'task_assignment')",
            name="ck_notifications_type",
        ),
        Index("ix_notifications_user_read", "user_id", "is_read"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    task_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    notification_type: Mapped[str] = mapped_column(
        String(30), nullable=False, index=True
    )
    dedup_key: Mapped[str] = mapped_column(String(255), nullable=False)
    is_read: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")
    task: Mapped[Optional["Task"]] = relationship("Task", back_populates="notifications")

    def __repr__(self) -> str:
        return (
            f"<Notification id={self.id} user_id={self.user_id} "
            f"type={self.notification_type!r} is_read={self.is_read}>"
        )
