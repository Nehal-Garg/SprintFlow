# SprintFlow — Future Improvements & Production Roadmap

With additional engineering time, SprintFlow can evolve from a clean small-team (3–10 users) Agile tracker into a multi-tenant production platform:

## 1. Database Migration to PostgreSQL & Alembic
- Migrate from single-file SQLite to **PostgreSQL** to support high concurrent writes, row-level locking, connection pooling (`pgbouncer`), and automated point-in-time backups.
- Introduce **Alembic** database migrations for versioned, reversible schema changes instead of startup `create_all()`.

## 2. Persistent Distributed Background Queue & Scheduled Scanner
- Replace in-process FastAPI `BackgroundTasks` with **Celery** (or **Dramatiq** / **ARQ**) backed by **Redis** so reminder jobs survive server restarts, scale across worker processes, and support dead-letter queues.
- Add a **periodic scheduler** (e.g., Celery Beat or cron) that scans upcoming/overdue tasks daily at a fixed time even when no user edits a task, plus optional email/Slack webhook delivery.

## 3. Real-Time Collaboration & Live Notifications
- Add **WebSockets** or **Server-Sent Events (SSE)** so Kanban card moves, new notifications, and activity updates propagate live to all connected teammates without manual refreshes.

## 4. Security Hardening
- Move JWTs to **`HttpOnly; Secure; SameSite=Lax` cookies** with refresh token rotation and server-side revocation on logout.
- Add **rate limiting** on `/auth/login` and `/auth/register`, optional email verification, and multi-tenant Organization/Workspace isolation.
- Expand RBAC with fine-grained permissions (Admin, Project Manager, Developer, Viewer).

## 5. Agile & Analytics Enhancements
- **Sprint Cycles & Burndown Charts:** Group User Stories into time-boxed Sprints (e.g., 2-week iterations) with velocity and burndown visualizations.
- **Task Comments, Subtasks & Attachments:** Threaded discussion on tasks and file attachments stored in object storage (S3/GCS).
- **CSV/PDF Sprint Reports:** Exportable sprint summaries and timesheet variance reports (`estimated_hours` vs. `actual_hours`).

## 6. Deployment, Observability & CI/CD
- Containerize frontend (Nginx) and backend (Gunicorn + Uvicorn workers) with **Docker** and `docker-compose.yml`.
- Add **GitHub Actions CI** running `pytest`, `ruff`/`flake8`, and `npm run build` on every pull request, plus Playwright browser E2E tests and structured JSON logging/metrics.
