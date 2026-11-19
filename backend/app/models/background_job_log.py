"""BackgroundJobLog ORM model for tracking async reminder processing results."""

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
    from app.models.task import Task


BACKGROUND_JOB_STATUSES = ("completed", "skipped", "failed")


class BackgroundJobLog(Base):
    """Operational log recording FastAPI BackgroundTasks reminder runs and retry counts."""

    __tablename__ = "background_job_logs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('completed', 'skipped', 'failed')",
            name="ck_background_job_logs_status",
        ),
        CheckConstraint(
            "attempts >= 0",
            name="ck_background_job_logs_attempts_non_negative",
        ),
        Index("ix_background_job_logs_task_status", "task_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_type: Mapped[str] = mapped_column(
        String(50), nullable=False, default="task_deadline_reminder", index=True
    )
    task_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("tasks.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    result_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, nullable=False, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False
    )

    # Relationships
    task: Mapped[Optional["Task"]] = relationship(
        "Task", back_populates="background_job_logs"
    )

    def __repr__(self) -> str:
        return (
            f"<BackgroundJobLog id={self.id} job_type={self.job_type!r} "
            f"task_id={self.task_id} status={self.status!r} attempts={self.attempts}>"
        )
