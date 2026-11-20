# SprintFlow — Technical Interview Q&A 

---

## Part 1: Technical Interview Questions & Defensible Answers

### 1. Why did you model `Project → User Story → Task` across separate normalized tables instead of one flat table?
Each level has distinct lifecycle semantics, attributes, and ownership: Projects have team memberships (`project_members`), start/end dates, and overall progress; User Stories have acceptance criteria, story points, and backlog workflow states (`Backlog → Done`); Tasks have granular assignees, estimated/actual hours, and Kanban execution states (`To Do → In Progress → In Review → Done`). Enforcing `NOT NULL` foreign keys (`user_stories.project_id`, `tasks.user_story_id`) with SQLite `PRAGMA foreign_keys=ON` and `ON DELETE CASCADE` prevents orphaned work items at the database layer—not just in application code.

### 2. SQLite disables foreign-key checks by default. How did you ensure referential integrity actually works?
In `backend/app/database.py`, I registered a SQLAlchemy `@event.listens_for(Engine, "connect")` listener that executes `PRAGMA foreign_keys=ON;` on every SQLite connection (both production and test engines). This is directly verified in `test_database_integrity.py`, which asserts `PRAGMA foreign_keys == 1`, confirms orphan inserts raise `IntegrityError`, and proves raw SQL `DELETE FROM projects` cascades cleanly down to `project_members`, `user_stories`, and `tasks`.

### 3. How does your authorization model prevent horizontal and vertical privilege escalation?
Every protected route depends on `get_current_user` (validating the `PyJWT` signature and expiry). Beyond authentication, every resource query enforces server-side membership:
- `GET /projects`, `GET /tasks`, `GET /dashboard/*`, and `GET /activity` filter strictly to `project_members.project_id` belonging to `current_user`.
- `require_project_member`, `require_story_access`, and `require_task_access` return `403 Forbidden` to non-members.
- `require_project_owner` restricts destructive project deletion and member management strictly to `owner` role members (with a guard preventing removal of the last owner).
- `GET /my-tasks` filters strictly to `assignee_id == current_user.id`, and `PATCH /notifications/{id}/read` enforces `notification.user_id == current_user.id`.
- Input Pydantic schemas set `ConfigDict(extra="forbid")` so clients cannot pass `id`, `created_by`, `project_id`, or `user_story_id` to tamper with ownership.

### 4. Walk through your asynchronous background workflow and its failure handling.
When a task is created, updated, or has its status changed, the FastAPI router schedules `process_task_deadline_reminder(task.id)` via `BackgroundTasks` and immediately returns the HTTP response. After the response is sent, the worker opens a **fresh independent SQLAlchemy session** (never reusing the closed request session), skips completed/unassigned/dateless tasks, classifies `overdue_task` vs `upcoming_deadline`, builds a deterministic `dedup_key`, and writes to `notifications`.
- **Duplicate Prevention:** Two layers—pre-insert lookup on `(user_id, dedup_key)` plus a SQLite `UNIQUE(user_id, dedup_key)` constraint catching race conditions.
- **Retries & Resilience:** Transient errors (`OperationalError`, `TimeoutError`, `OSError`) retry up to 3 times with bounded exponential backoff (`0.2s, 0.4s`); non-retryable errors fail fast. Exceptions are caught and logged to `background_job_logs` (`completed | skipped | failed`, with `attempts`), so notification issues never break the main CRUD request.

### 5. What are the limitations of FastAPI `BackgroundTasks`, and how would you scale this?
FastAPI `BackgroundTasks` runs **in-process** in memory inside Uvicorn. It is **not** a persistent distributed job queue—if the server crashes or restarts while a reminder is queued, that pending run is lost. Also, it is event-triggered on task mutations rather than wall-clock scheduled. For production scale, I would migrate to **Celery or Dramatiq + Redis** for durable worker queues, add **Celery Beat** for daily scheduled deadline scans, and move SQLite to **PostgreSQL** with **Alembic** migrations.

### 6. How does your Kanban drag-and-drop handle backend failures?
In `KanbanBoard.jsx`, dragging a task card (or changing its quick status selector) saves a snapshot of the current tasks array, updates the column optimistically for zero-lag UX, and sends `PATCH /tasks/{id}/status`. On success, it replaces the card with the authoritative server response and shows a success toast. If the API fails (e.g., network error or 403), it immediately rolls back to the saved snapshot and displays an error toast.

### 7. Why did you keep `notifications.task_id` and `activity_logs.project_id` as `ON DELETE SET NULL`?
Users still need to see historical activity ("Deleted project X") and past notifications even if the underlying task or project is later deleted. Using `ON DELETE SET NULL` keeps referential integrity intact without breaking deletion cascades or erasing audit trails.

### 8. How did you verify security and test isolation?
All 36 Pytest tests run against isolated per-test temporary SQLite databases (`tmp_path`), overriding both `get_db` and `get_session_factory` so even `BackgroundTasks` runs against the isolated test DB. We explicitly test bcrypt hash verification, non-exposure of `password_hash`, expired/tampered JWTs, cross-project `403` isolation, cross-user notification `403` isolation, mass-assignment `422` rejection, and parameterized ORM immunity to SQL injection strings.



>
> All architecture notes, ER diagrams, API docs, security considerations, design tradeoffs, and honest AI usage disclosures are documented in the repository. Thank you for watching!"
