# SprintFlow — Technical Interview Q&A & Screen Recording Demo Script

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

---

## Part 2: 5–7 Minute Screen Recording Script (With Voice Narration)

> **Preparation Before Recording:**
> 1. Start backend (`uvicorn app.main:app --reload --port 8000`) and frontend (`npm run dev` on port `5173`).
> 2. Optionally run `backend\.venv\Scripts\python.exe backend\seed_demo.py` OR start fresh to register live on camera.
> 3. Keep 3 browser tabs ready: `http://localhost:5173` (SprintFlow), `http://localhost:8000/docs` (Swagger UI), and your terminal (ready to run `pytest`).

---

### [0:00 – 0:45] Introduction, Objective & Tech Stack
*(Show Login screen and briefly pan to README / Architecture diagram)*
> "Hi, I'm [Your Name], and this is **SprintFlow** — a full-stack Agile Project Management Tool I built for small engineering teams of 3 to 10 developers as part of the KPIT Full-Stack Intern assignment.
>
> The core goal of SprintFlow is clean hierarchical work tracking: **Project → User Story → Task**, backed by a real REST API and persistent relational database — no dummy frontend data.
>
> On the frontend, I used **React, Vite, Tailwind CSS, React Router, Axios, and Recharts** with a clean black, green, and white enterprise SaaS design system. On the backend, I built modular **FastAPI** APIs with **SQLAlchemy 2.x ORM, Pydantic v2 validation, bcrypt + PyJWT authentication, SQLite** with enforced foreign keys, and **FastAPI BackgroundTasks** for asynchronous deadline reminders."

---

### [0:45 – 1:30] Authentication & Protected Navigation
*(Click "Create an account" or log in as `arjun@sprintflow.dev` / `DemoPass123`)*
> "Let's start with authentication. Registration validates email format and password strength, hashes passwords using **bcrypt with 12 salt rounds**, and never stores plain-text credentials or exposes password hashes in API responses.
>
> Logging in issues a signed **JWT Bearer token** attached automatically by our centralized Axios client. All private routes are protected both in React Router and on the FastAPI backend."

---

### [1:30 – 2:30] Dynamic Dashboard Analytics
*(Show Dashboard page, hover over Recharts charts, scroll down to live lists)*
> "After signing in, we land on the **Dashboard**. Every single number here — Total Projects, Active Projects, User Stories, Total Tasks, Completed Tasks, and Overdue Tasks — is dynamically aggregated from SQLite via `GET /dashboard/summary` and `GET /dashboard/project-progress`, scoped strictly to projects I'm a member of.
>
> Below the KPIs, we have four **Recharts** visualizations: Tasks by Status, Project Progress percentage, Completed vs. Pending ratio, and Task Priority Distribution — followed by live Recent Projects, My Assigned Tasks, Upcoming Deadlines, Overdue Tasks, Recently Updated Tasks, and Recent Activity."

---

### [2:30 – 4:00] Hierarchical Workflow: Project → User Story → Task & Membership
*(Navigate to Projects → Create/Open a Project → Add Member → Add Story → Add Task with due date tomorrow/yesterday)*
> "Now let's walk through the core **Project → User Story → Task** hierarchy. In **Projects**, I can search, filter by status, see real-time completion progress bars, or create a new project.
>
> Opening a project takes us to **Project Details**. On the right panel, because I'm the project **Owner**, I can manage project members—adding or removing teammates—while non-owner members can collaborate on stories and tasks without being able to delete the project or alter team membership. Outsiders receive a `403 Forbidden` from the backend.
>
> Under User Stories, I can create a story with acceptance criteria, story points, priority, and assignee. Inside each expanded story, we manage child **Tasks** with assignees, estimated vs. actual hours, and due dates. Watch what happens when I create a task assigned to a teammate with a deadline tomorrow (or overdue yesterday): the API responds immediately while scheduling our **FastAPI BackgroundTasks** deadline reminder workflow asynchronously."

---

### [4:00 – 4:50] Kanban Board & My Tasks
*(Navigate to Kanban Board → Drag a task from `To Do` to `In Progress` or `Done` → Refresh page → Show My Tasks)*
> "Moving to the **Kanban Board**, all tasks from my accessible projects appear across four columns: To Do, In Progress, In Review, and Done. Each card displays the task title, project, user story, assignee, priority, and deadline.
>
> When I drag a card to **Done**, the UI updates optimistically and sends `PATCH /tasks/{id}/status` to FastAPI. If the backend were to reject the change, the UI automatically rolls back and notifies the user. Refreshing the page proves the update is persisted in SQLite, and our project progress recalculates automatically.
>
> Under **My Tasks**, the `/my-tasks` endpoint strictly isolates tasks assigned only to the logged-in user, highlighting overdue and due-soon deadlines."

---

### [4:50 – 5:45] Asynchronous Notifications, Background Job Logs & Activity Log
*(Navigate to Notifications → Click "Background Job Logs" → Mark a notification read → Navigate to Activity Log)*
> "Notice the green unread badge in the top navigation bar. On the **Notifications** page, we see persistent SQLite alerts for **Task Assignment**, **Upcoming Deadlines**, and **Overdue Tasks**.
>
> Clicking **Background Job Logs** reveals the `background_job_logs` audit table, showing each FastAPI `BackgroundTasks` run, attempt count, and duplicate-prevention skips. Every reminder uses a deterministic `dedup_key` backed by a SQLite `UNIQUE(user_id, dedup_key)` constraint, plus bounded exponential retries for transient database locks. I also transparently document in the repo that FastAPI `BackgroundTasks` runs in-process—so queued jobs do not survive server restarts—and outline how to upgrade to Celery + Redis in production.
>
> Next, the **Activity Log** gives a chronological audit trail across project, user story, and task lifecycle events."

---

### [5:45 – 6:35] Swagger UI, Database Design & Automated Pytest Suite
*(Switch to `http://localhost:8000/docs`, scroll endpoints; switch to terminal and run `pytest`)*
> "Switching to **`http://localhost:8000/docs`**, FastAPI generates complete interactive OpenAPI/Swagger documentation covering Authentication, Projects, Membership, User Stories, Tasks, My Tasks, Notifications, Activity, and Dashboard endpoints.
>
> Underneath, our SQLite database enforces `PRAGMA foreign_keys=ON` on every connection across 8 normalized tables, with cascading deletes preventing orphaned stories or tasks while preserving audit history via `ON DELETE SET NULL`.
>
> Finally, let's run our automated **Pytest** suite. *[Run pytest]* All **36 tests pass** against isolated temporary SQLite databases—covering authentication, password hashing, JWT expiry, CRUD, cascading integrity, authorization boundaries, background reminders, deduplication, and simulated retry recovery.
>
> All architecture notes, ER diagrams, API docs, security considerations, design tradeoffs, and honest AI usage disclosures are documented in the repository. Thank you for watching!"
