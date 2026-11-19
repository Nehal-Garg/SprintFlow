# SprintFlow — System & Workflow Flowcharts

> Visual flowcharts rendered natively on GitHub covering SprintFlow's full-stack architecture, hierarchical Agile workflow (`Project → User Story → Task`), and asynchronous FastAPI `BackgroundTasks` reminder pipeline.

---

## 1. Full-Stack System Architecture Flow

```mermaid
flowchart LR
    FE["React + Vite SPA (10 Pages, Tailwind, Recharts)"]
    AX["Axios Client (Bearer JWT + 401 Handler)"]
    API["FastAPI Routers (34 Routes + Swagger /docs)"]
    GUARD["Auth & Membership Guard (PyJWT + Owner/Member 401/403)"]
    SVC["Domain Services (CRUD, Progress, Activity Log)"]
    BG["FastAPI BackgroundTasks (Post-Response Worker)"]
    DB[("SQLite + SQLAlchemy 2.x (PRAGMA foreign_keys=ON, 8 Tables)")]

    FE -->|"REST JSON"| AX
    AX -->|"Authorization: Bearer JWT"| API
    API --> GUARD
    GUARD --> SVC
    SVC -->|"Parameterized ORM"| DB
    SVC -.->|"Schedule async"| BG
    BG -.->|"Fresh DB Session"| DB
```

---

## 2. Hierarchical Work Tracking Flow (`Project → User Story → Task`)

```mermaid
flowchart TD
    AUTH["1. Register / Login (bcrypt 12-round + PyJWT)"]
    PROJ["2. Project (Creator = Owner, Team Members)"]
    STORY["3. User Story (Acceptance Criteria, Story Points, Priority)"]
    TASK["4. Task (Assignee, Est/Actual Hours, Due Date, Status)"]

    KANBAN["Kanban Board (Drag & Drop + Optimistic Rollback)"]
    MYTASKS["My Tasks (Strictly Self-Assigned + Overdue Alerts)"]
    DASH["Live Dashboard (7 KPIs + 4 Recharts Charts)"]
    AUDIT["Notifications & Chronological Activity Log"]

    AUTH --> PROJ
    PROJ -->|"1 : N (ON DELETE CASCADE)"| STORY
    STORY -->|"1 : N (ON DELETE CASCADE)"| TASK
    TASK --> KANBAN
    TASK --> MYTASKS
    TASK --> DASH
    TASK --> AUDIT
```

---

## 3. Asynchronous Background Reminder Pipeline (`FastAPI BackgroundTasks`)

```mermaid
flowchart TD
    TRIG["Task Created / Updated / Status Changed"]
    RESP["HTTP Response Returned Immediately (Non-Blocking)"]
    SESS["Background Worker Opens Fresh SQLAlchemy Session"]
    ELIG{"Has Assignee, Due Date, and Status != Done?"}
    SKIP1["Log background_job_logs (status = skipped)"]
    CLASS{"Compare due_date with Today"}
    OVER["Type = overdue_task"]
    UPCOM{"due_date <= Today + 2 Days?"}
    SOON["Type = upcoming_deadline"]
    DEDUP["2-Layer Dedup: Pre-Check + UNIQUE(user_id, dedup_key)"]
    EXISTS{"Already Exists?"}
    RETRY["Bounded Retry Loop (Max 3 Attempts, Exponential Backoff)"]
    SAVE["Persist Notification + Log background_job_logs (completed)"]
    FAIL["Catch Exception + Log background_job_logs (failed)"]

    TRIG --> RESP
    TRIG -.-> SESS
    SESS --> ELIG
    ELIG -- "No" --> SKIP1
    ELIG -- "Yes" --> CLASS
    CLASS -- "due_date < Today" --> OVER --> DEDUP
    CLASS -- "due_date >= Today" --> UPCOM
    UPCOM -- "No" --> SKIP1
    UPCOM -- "Yes" --> SOON --> DEDUP
    DEDUP --> EXISTS
    EXISTS -- "Yes" --> SKIP1
    EXISTS -- "No" --> RETRY
    RETRY -- "Success" --> SAVE
    RETRY -- "Retries Exhausted / Error" --> FAIL
```

> **Architectural Tradeoff:** FastAPI `BackgroundTasks` runs in-process after the HTTP response; queued reminders do not survive server restarts. For production scale, migrate to **Celery / Dramatiq + Redis** with a periodic scheduler (see [FUTURE_IMPROVEMENTS.md](FUTURE_IMPROVEMENTS.md)).
