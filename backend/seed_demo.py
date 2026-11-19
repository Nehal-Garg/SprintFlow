"""Optional CLI script to populate SprintFlow with realistic small-team demo data.

Usage (from project root):
    backend\\.venv\\Scripts\\python.exe backend\\seed_demo.py

This script is idempotent: if the demo users already exist, it exits without duplicating data.
"""

import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import select

from app.background.deadline_reminders import process_task_deadline_reminder
from app.core.security import hash_password
from app.database import SessionLocal, init_db
from app.models import Project, ProjectMember, Task, User, UserStory
from app.services.activity_service import record_activity
from app.services.notification_service import create_task_assignment_notification


def _get_or_create_user(db, *, full_name: str, email: str, password: str) -> User:
    """Fetch existing user by email or create a new one without raising IntegrityError."""
    normalized = email.strip().lower()
    existing = db.scalar(select(User).where(User.email == normalized))
    if existing is not None:
        return existing
    user = User(
        full_name=full_name,
        email=normalized,
        password_hash=hash_password(password),
    )
    db.add(user)
    db.flush()
    return user


def seed() -> None:
    init_db()
    db = SessionLocal()
    try:
        arjun = _get_or_create_user(
            db, full_name="Arjun Mehta", email="arjun@sprintflow.dev", password="DemoPass123"
        )
        priya = _get_or_create_user(
            db, full_name="Priya Nair", email="priya@sprintflow.dev", password="DemoPass123"
        )
        rohan = _get_or_create_user(
            db, full_name="Rohan Verma", email="rohan@sprintflow.dev", password="DemoPass123"
        )

        existing_demo_proj = db.scalar(
            select(Project).where(
                Project.name == "E-Commerce Platform",
                Project.created_by == arjun.id,
            )
        )
        if existing_demo_proj is not None:
            db.commit()
            print("Demo data already present. Skipping duplicate project seed.")
            return

        today = date.today()
        p1 = Project(
            name="E-Commerce Platform",
            description="Customer-facing retail web portal with auth, catalog, and checkout.",
            start_date=today - timedelta(days=14),
            end_date=today + timedelta(days=30),
            status="Active",
            created_by=arjun.id,
        )
        p2 = Project(
            name="Internal Analytics Dashboard",
            description="Telemetry reporting workspace for engineering leadership.",
            start_date=today - timedelta(days=30),
            end_date=today + timedelta(days=10),
            status="Planning",
            created_by=priya.id,
        )
        db.add_all([p1, p2])
        db.flush()

        db.add_all(
            [
                ProjectMember(project_id=p1.id, user_id=arjun.id, role="owner"),
                ProjectMember(project_id=p1.id, user_id=priya.id, role="member"),
                ProjectMember(project_id=p1.id, user_id=rohan.id, role="member"),
                ProjectMember(project_id=p2.id, user_id=priya.id, role="owner"),
                ProjectMember(project_id=p2.id, user_id=arjun.id, role="member"),
            ]
        )

        record_activity(
            db,
            user_id=arjun.id,
            project_id=p1.id,
            action="project_created",
            entity_type="project",
            entity_id=p1.id,
            description=f"Created project '{p1.name}'",
        )
        record_activity(
            db,
            user_id=priya.id,
            project_id=p2.id,
            action="project_created",
            entity_type="project",
            entity_id=p2.id,
            description=f"Created project '{p2.name}'",
        )

        s1 = UserStory(
            project_id=p1.id,
            title="User Authentication",
            description="Allow customers to register, sign in, and manage sessions securely.",
            acceptance_criteria="Passwords hashed with bcrypt; JWT issued on valid login; 401 on invalid credentials.",
            priority="Critical",
            status="In Progress",
            story_points=8,
            assigned_to=arjun.id,
            due_date=today + timedelta(days=5),
        )
        s2 = UserStory(
            project_id=p1.id,
            title="Product Management",
            description="Browse product catalog, search inventory, and view product details.",
            acceptance_criteria="Search returns matching items within 200ms; detail page shows specs and pricing.",
            priority="High",
            status="To Do",
            story_points=5,
            assigned_to=priya.id,
            due_date=today + timedelta(days=12),
        )
        s3 = UserStory(
            project_id=p2.id,
            title="Sprint Velocity Metrics",
            description="Aggregate completed story points and overdue tasks per sprint.",
            acceptance_criteria="Dashboard charts refresh dynamically from live database queries.",
            priority="Medium",
            status="In Progress",
            story_points=5,
            assigned_to=priya.id,
            due_date=today + timedelta(days=7),
        )
        db.add_all([s1, s2, s3])
        db.flush()

        tasks = [
            Task(
                user_story_id=s1.id,
                title="Design login interface",
                description="Create responsive black/green/white login and register screens.",
                assignee_id=priya.id,
                priority="High",
                status="Done",
                start_date=today - timedelta(days=6),
                due_date=today - timedelta(days=2),
                estimated_hours=4.0,
                actual_hours=3.5,
            ),
            Task(
                user_story_id=s1.id,
                title="Develop registration API",
                description="Implement POST /auth/register with Pydantic email/password checks.",
                assignee_id=arjun.id,
                priority="Critical",
                status="In Review",
                start_date=today - timedelta(days=3),
                due_date=today + timedelta(days=1),
                estimated_hours=5.0,
                actual_hours=4.5,
            ),
            Task(
                user_story_id=s1.id,
                title="Implement password validation",
                description="Enforce strength rules and constant-time bcrypt verification.",
                assignee_id=rohan.id,
                priority="High",
                status="In Progress",
                start_date=today - timedelta(days=4),
                due_date=today - timedelta(days=1),
                estimated_hours=3.0,
                actual_hours=2.0,
            ),
            Task(
                user_story_id=s2.id,
                title="Develop product listing",
                description="Paginated grid view with status and category filters.",
                assignee_id=priya.id,
                priority="Medium",
                status="To Do",
                start_date=today,
                due_date=today + timedelta(days=6),
                estimated_hours=6.0,
            ),
            Task(
                user_story_id=s2.id,
                title="Implement product search",
                description="Debounced keyword search integrated with backend API.",
                assignee_id=arjun.id,
                priority="Medium",
                status="To Do",
                start_date=today + timedelta(days=1),
                due_date=today + timedelta(days=8),
                estimated_hours=4.0,
            ),
            Task(
                user_story_id=s3.id,
                title="Build summary KPI aggregation query",
                description="Compute total, completed, pending, and overdue task counts.",
                assignee_id=arjun.id,
                priority="High",
                status="Done",
                start_date=today - timedelta(days=5),
                due_date=today - timedelta(days=1),
                estimated_hours=3.5,
                actual_hours=3.0,
            ),
        ]
        db.add_all(tasks)
        db.flush()

        for t in tasks:
            proj = p1 if t.user_story_id in (s1.id, s2.id) else p2
            record_activity(
                db,
                user_id=arjun.id,
                project_id=proj.id,
                action="task_created",
                entity_type="task",
                entity_id=t.id,
                description=f"Created task '{t.title}'",
            )
            if t.assignee_id:
                create_task_assignment_notification(
                    db,
                    task=t,
                    project_name=proj.name,
                    assignee_id=t.assignee_id,
                    assigned_by_name=arjun.full_name,
                )

        db.commit()
        task_ids = [t.id for t in tasks]
        db.close()

        # Execute the real background reminder worker on all seeded tasks
        for tid in task_ids:
            process_task_deadline_reminder(tid)

        print("Seeded SprintFlow demo data successfully.")
        print("Demo accounts (password: DemoPass123):")
        print("  - arjun@sprintflow.dev (Owner of E-Commerce Platform)")
        print("  - priya@sprintflow.dev (Owner of Internal Analytics Dashboard)")
        print("  - rohan@sprintflow.dev (Member of E-Commerce Platform)")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
