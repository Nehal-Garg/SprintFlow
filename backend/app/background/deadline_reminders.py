"""Task deadline reminder background workflow using FastAPI BackgroundTasks.

IMPORTANT ARCHITECTURAL NOTE:
FastAPI BackgroundTasks runs in-process after the HTTP response is sent.
It is NOT a persistent distributed job queue: if the Python/Uvicorn process
restarts or crashes before a queued task finishes, that in-flight reminder is lost.
For production multi-worker deployments, migrate to a persistent queue (e.g., Celery/Dramatiq + Redis)
with a wall-clock periodic scheduler.
"""

import logging
import time
from datetime import date, timedelta
from typing import Callable, Optional

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.database import SessionLocal
from app.models import BackgroundJobLog, Notification, Task, UserStory

logger = logging.getLogger("sprintflow.background")

RETRYABLE_EXCEPTIONS = (OperationalError, TimeoutError, OSError)


def build_deadline_dedup_key(
    notification_type: str,
    task_id: int,
    user_id: int,
    due_date: date,
) -> str:
    """Deterministic idempotency key preventing duplicate deadline notifications."""
    return f"{notification_type}:task:{task_id}:user:{user_id}:due:{due_date.isoformat()}"


def _persist_job_log(
    session_factory: Callable[[], Session],
    *,
    task_id: Optional[int],
    status: str,
    attempts: int,
    result_summary: str,
    error_message: Optional[str] = None,
) -> None:
    """Safely persist a BackgroundJobLog entry without ever crashing the caller."""
    log_db: Optional[Session] = None
    try:
        log_db = session_factory()
        # Verify task still exists before attaching FK
        safe_task_id = task_id if (task_id and log_db.get(Task, task_id) is not None) else None
        log_entry = BackgroundJobLog(
            job_type="task_deadline_reminder",
            task_id=safe_task_id,
            status=status,
            attempts=attempts,
            result_summary=result_summary,
            error_message=error_message[:1000] if error_message else None,
        )
        log_db.add(log_entry)
        log_db.commit()
    except Exception as exc:  # pragma: no cover - defensive fallback
        logger.error("Unable to persist background job log: %s", type(exc).__name__)
        if log_db is not None:
            log_db.rollback()
    finally:
        if log_db is not None:
            log_db.close()


def process_task_deadline_reminder(
    task_id: int,
    *,
    session_factory: Optional[Callable[[], Session]] = None,
    max_retries: Optional[int] = None,
    base_delay_seconds: Optional[float] = None,
    reminder_days: Optional[int] = None,
    today_override: Optional[date] = None,
) -> str:
    """Evaluate a task's deadline in the background and persist notifications with retries & dedup.

    Returns a short status string ('completed', 'skipped', or 'failed') for observability and testing.
    Never raises uncaught exceptions so background failures cannot disrupt API operations.
    """
    settings = get_settings()
    factory = session_factory or SessionLocal
    retries = max_retries if max_retries is not None else settings.background_max_retries
    delay = (
        base_delay_seconds
        if base_delay_seconds is not None
        else settings.background_retry_base_delay_seconds
    )
    window_days = (
        reminder_days if reminder_days is not None else settings.deadline_reminder_days
    )
    today = today_override or date.today()

    attempts = 0
    last_error: Optional[str] = None

    while attempts < retries:
        attempts += 1
        db: Optional[Session] = None
        try:
            db = factory()
            stmt = (
                select(Task)
                .options(joinedload(Task.user_story).joinedload(UserStory.project))
                .where(Task.id == task_id)
            )
            task = db.scalar(stmt)

            if task is None:
                db.close()
                _persist_job_log(
                    factory,
                    task_id=None,
                    status="skipped",
                    attempts=attempts,
                    result_summary=f"Task {task_id} no longer exists.",
                )
                return "skipped"

            if task.status == "Done":
                db.close()
                _persist_job_log(
                    factory,
                    task_id=task.id,
                    status="skipped",
                    attempts=attempts,
                    result_summary="Task is already Done; no deadline reminder required.",
                )
                return "skipped"

            if task.assignee_id is None or task.due_date is None:
                db.close()
                _persist_job_log(
                    factory,
                    task_id=task.id,
                    status="skipped",
                    attempts=attempts,
                    result_summary="Task lacks an assignee or due_date; skipped reminder.",
                )
                return "skipped"

            project_name = (
                task.user_story.project.name
                if task.user_story and task.user_story.project
                else "SprintFlow"
            )

            if task.due_date < today:
                notification_type = "overdue_task"
                days_late = (today - task.due_date).days
                day_label = "day" if days_late == 1 else "days"
                message = (
                    f"Overdue task: '{task.title}' in '{project_name}' was due on "
                    f"{task.due_date.isoformat()} ({days_late} {day_label} overdue)."
                )
            elif task.due_date <= today + timedelta(days=window_days):
                notification_type = "upcoming_deadline"
                days_left = (task.due_date - today).days
                due_phrase = (
                    "today"
                    if days_left == 0
                    else f"in {days_left} {'day' if days_left == 1 else 'days'}"
                )
                message = (
                    f"Upcoming deadline: '{task.title}' in '{project_name}' is due "
                    f"{due_phrase} ({task.due_date.isoformat()})."
                )
            else:
                db.close()
                _persist_job_log(
                    factory,
                    task_id=task.id,
                    status="skipped",
                    attempts=attempts,
                    result_summary=(
                        f"Task due_date {task.due_date.isoformat()} is outside the "
                        f"{window_days}-day reminder window."
                    ),
                )
                return "skipped"

            dedup_key = build_deadline_dedup_key(
                notification_type,
                task.id,
                task.assignee_id,
                task.due_date,
            )

            # Layer 1 duplicate prevention: check before insert
            existing = db.scalar(
                select(Notification).where(
                    Notification.user_id == task.assignee_id,
                    Notification.dedup_key == dedup_key,
                )
            )
            if existing is not None:
                db.close()
                _persist_job_log(
                    factory,
                    task_id=task.id,
                    status="skipped",
                    attempts=attempts,
                    result_summary=f"Duplicate {notification_type} reminder prevented.",
                )
                return "skipped"

            # Layer 2 duplicate prevention: DB UNIQUE(user_id, dedup_key)
            notification = Notification(
                user_id=task.assignee_id,
                task_id=task.id,
                message=message,
                notification_type=notification_type,
                dedup_key=dedup_key,
                is_read=False,
            )
            db.add(notification)
            db.commit()
            db.close()

            _persist_job_log(
                factory,
                task_id=task.id,
                status="completed",
                attempts=attempts,
                result_summary=f"Created {notification_type} notification for user {task.assignee_id}.",
            )
            return "completed"

        except IntegrityError:
            if db is not None:
                db.rollback()
                db.close()
            _persist_job_log(
                factory,
                task_id=task_id,
                status="skipped",
                attempts=attempts,
                result_summary="Duplicate reminder prevented by database unique constraint.",
            )
            return "skipped"

        except RETRYABLE_EXCEPTIONS as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            logger.warning(
                "Retryable background reminder error on task %s (attempt %d/%d): %s",
                task_id,
                attempts,
                retries,
                type(exc).__name__,
            )
            if db is not None:
                db.rollback()
                db.close()
            if attempts < retries and delay > 0:
                time.sleep(delay * (2 ** (attempts - 1)))

        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            logger.error(
                "Non-retryable background reminder error on task %s: %s",
                task_id,
                type(exc).__name__,
            )
            if db is not None:
                db.rollback()
                db.close()
            _persist_job_log(
                factory,
                task_id=task_id,
                status="failed",
                attempts=attempts,
                result_summary="Non-retryable error during deadline reminder processing.",
                error_message=last_error,
            )
            return "failed"

    # Retries exhausted
    _persist_job_log(
        factory,
        task_id=task_id,
        status="failed",
        attempts=attempts,
        result_summary=f"Exhausted {retries} bounded retry attempts.",
        error_message=last_error,
    )
    return "failed"
