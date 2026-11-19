# SprintFlow — Design Decisions & Engineering Tradeoffs

Every architectural choice in SprintFlow was made deliberately for the target context: a **small Agile development team of 3–10 users** requiring full-stack clarity, strong relational integrity, and zero unnecessary operational overhead.

---

## 1. Technology Stack Rationale

- **FastAPI + Pydantic v2:** Chosen for automatic OpenAPI/Swagger documentation (`/docs`), clean dependency injection (`Depends`), strict runtime schema validation, and built-in `BackgroundTasks` support.
- **SQLAlchemy 2.x ORM:** Provides type-safe declarative models, parameterized queries (eliminating SQL injection risks), clean relationship traversal (`Project → UserStory → Task`), and straightforward portability to PostgreSQL later without rewriting business logic.
- **React + Vite + Tailwind CSS + Recharts:** Fast build pipeline, clean component reuse, consistent KPIT-inspired Black/Green/White design tokens without heavy UI framework bloat, and declarative charts for dynamic analytics.
- **Direct `bcrypt` + `PyJWT`:** Used directly instead of legacy wrapper libraries (`passlib` / `python-jose`) to avoid Python 3.11+ deprecation warnings and maintain transparent, auditable cryptographic code.
- **Native HTML5 Drag-and-Drop (Kanban):** Used alongside an accessible status dropdown fallback on every card rather than adding a heavy third-party DnD framework. This keeps bundle size lean while still supporting optimistic updates and rollback on API failure.

---

## 2. Why SQLite Was Chosen

- **Zero Infrastructure Overhead:** For a 3–10 user team, a single-file ACID-compliant SQLite database starts instantly with zero external DB server setup.
- **Strict Relational Enforcement:** Because SQLite disables foreign-key checks by default, SprintFlow explicitly attaches an `@event.listens_for(Engine, "connect")` hook executing `PRAGMA foreign_keys=ON;` on every connection. Combined with explicit `CHECK` and `UNIQUE` constraints, SQLite enforces full relational integrity.
- **Tradeoff:** SQLite supports only one concurrent writer at a time and is tied to a single host filesystem. Under high write concurrency or multi-instance horizontal scaling, migrating `DATABASE_URL` to PostgreSQL is required.

---

## 3. Database Relationship & Audit Table Decisions

- **Strict 3-Level Hierarchy (`Project → UserStory → Task`):** Enforced via `NOT NULL` foreign keys and `ON DELETE CASCADE` so orphaned user stories or tasks are impossible both via API and at the SQL level.
- **`ON DELETE SET NULL` on Audit & Notification FKs:** Deleting a task or project preserves the user's notification history (`notifications.task_id = NULL`), activity timeline (`activity_logs.project_id = NULL`), and job logs (`background_job_logs.task_id = NULL`).
- **8th Operational Table (`background_job_logs`):** Added alongside the 7 core tables so background reminder execution attempts, deduplication skips, and failures are persistently auditable and verifiable in both automated tests and the UI.

---

## 4. Background Workflow Tradeoffs (`FastAPI BackgroundTasks`)

- **Why `BackgroundTasks`:** Meets the assignment's asynchronous processing requirement cleanly without introducing Redis, RabbitMQ, or Celery worker infrastructure for a 3–10 user app. Non-critical deadline checks execute after the HTTP response is flushed, keeping task creation/update latency low.
- **Safety Mechanisms Built In:**
  - Dedicated DB session per background execution (never reuses the closed request session).
  - Two-layer deduplication (application pre-check + SQLite `UNIQUE(user_id, dedup_key)`).
  - Bounded exponential retries (`max 3 attempts`) for transient `OperationalError` locks; fail-fast for non-retryable errors.
  - Full exception isolation so reminder failures never break main CRUD requests.
- **Explicit Limitations:**
  1. **No Persistence Across Restarts:** `BackgroundTasks` lives in-process in memory. If Uvicorn crashes or restarts while a task is queued or mid-retry, that pending reminder is lost.
  2. **Event-Triggered Only:** Reminders run when tasks are created, updated, or transitioned—not via a persistent wall-clock midnight cron scanner. A task whose deadline quietly passes without any edit won't trigger a new reminder until evaluated or until a scheduled daemon is added.

---

## 5. Authorization Role Model

- **Project Owner vs. Member:** Creating a project automatically enrolls the creator as `owner`. Both owners and members can collaborate on project details, stories, and tasks. Only owners can delete the project or add/remove team members (with a guard preventing removal of the sole remaining owner).
- **Assignee Membership Invariant:** Assigning a user story or task validates that the assignee is already a member of that project; removing a member automatically clears their assignments inside that project.
- **Mass-Assignment Protection:** Every input Pydantic schema uses `ConfigDict(extra="forbid")` so clients cannot sneak `id`, `created_by`, `project_id`, or `user_story_id` into JSON payloads to bypass authorization boundaries.
