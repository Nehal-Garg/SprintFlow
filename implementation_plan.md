# SprintFlow — Implementation Plan & Requirement Traceability

> **Application:** SprintFlow — Agile Project Management Tool for Small Teams (3–10 Users)  
> **Workspace:** `d:\sprintflow`  
> **Architecture Reference:** [architecture.md](file:///d:/sprintflow/architecture.md)

---

## 1. Workspace Inspection Findings

The workspace `d:\sprintflow` is currently clean (empty directory), and all required runtimes are available locally:

| Tool / Runtime | Detected Version | Role |
|---|---|---|
| Python | `3.11.9` (`pip 24.0`) | FastAPI backend, SQLAlchemy ORM, Pytest |
| Node.js | `v24.16.0` | Frontend build & dev server |
| npm | `11.13.0` | React/Vite/Tailwind dependency management |
| Git | `2.54.0` | Version control & GitHub submission readiness |

---

## 2. Technology Stack & Dependency Decisions

Strictly adhering to the requested stack with zero unnecessary frameworks:

- **Backend:** `fastapi`, `uvicorn[standard]`, `sqlalchemy` (2.x), `pydantic`, `pydantic-settings`, `email-validator`, `PyJWT`, `bcrypt`, `python-dotenv`, `pytest`, `httpx`
  - *Engineering note:* Using `bcrypt` directly + `PyJWT` avoids legacy `passlib`/`python-jose` compatibility warnings on Python 3.11 while maintaining industry-standard salted password hashing and RFC 7519 JWT validation.
- **Database:** SQLite (`sprintflow.db`) with `PRAGMA foreign_keys=ON` enforced on every connection.
- **Background Processing:** FastAPI `BackgroundTasks` (in-process, non-blocking post-response execution with dedicated DB session, bounded retries, deduplication, and `background_job_logs` audit trail).
- **Frontend:** `react`, `react-dom`, `react-router-dom`, `axios`, `recharts`, `tailwindcss`, `vite`, `lucide-react` (lightweight tree-shakable icons only—no UI component framework).
  - *Engineering note:* Kanban drag-and-drop will use the native HTML5 Drag-and-Drop API (plus accessible keyboard/dropdown fallback) rather than adding heavy third-party DnD libraries.

---

## 3. Ten-Phase Execution Plan

Work will proceed strictly in the 10 specified phases, reporting files created/modified, engineering decisions, and test/validation output after each phase.

### Phase 1: Workspace Inspection, Requirements Analysis, Plan & Architecture *(Current Phase)*
- Inspect workspace & runtime environment.
- Produce [implementation_plan.md](file:///d:/sprintflow/implementation_plan.md) and [architecture.md](file:///d:/sprintflow/architecture.md) with full requirement traceability.
- **Gate:** Wait for user review and approval before starting Phase 2.

### Phase 2: Database Setup, SQLAlchemy Models & Relationships
- Initialize Git repository, `.gitignore`, and `.env.example`.
- Create Python virtual environment (`backend/.venv`) and `backend/requirements.txt`.
- Implement `backend/app/core/config.py` (environment-driven `SECRET_KEY`, `DATABASE_URL`, `CORS_ORIGINS`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `DEADLINE_REMINDER_DAYS`).
- Implement `backend/app/database.py` with SQLite engine + `PRAGMA foreign_keys=ON` event hook + `SessionLocal` + `Base`.
- Implement all SQLAlchemy ORM models under `backend/app/models/`:
  1. `User` (`users`)
  2. `Project` & `ProjectMember` (`projects`, `project_members`)
  3. `UserStory` (`user_stories`)
  4. `Task` (`tasks`)
  5. `Notification` (`notifications`, with `dedup_key` + `UniqueConstraint("user_id", "dedup_key")`)
  6. `ActivityLog` (`activity_logs`)
  7. `BackgroundJobLog` (`background_job_logs` — operational log for reminder processing attempts & outcomes)
- Verify schema creation, foreign-key enforcement, and cascading deletes via a verification script/pytest check.

### Phase 3: FastAPI Backend, Authentication & Core CRUD APIs
- Implement `backend/app/core/security.py` (`hash_password`, `verify_password`, `create_access_token`, `decode_access_token`).
- Implement `backend/app/core/dependencies.py` (`get_db`, `get_current_user`, `verify_project_membership`, `get_accessible_project_ids`).
- Implement Pydantic v2 schemas in `backend/app/schemas/` with strict validation (email format, password strength, enum constraints for statuses/priorities, non-negative hours/points, date sanity).
- Implement modular service layer (`backend/app/services/`) and routers (`backend/app/routers/`):
  - **Auth & Users:** `POST /auth/register`, `POST /auth/login`, `GET /auth/me`, `PUT /auth/me`, `PUT /auth/me/password`, `GET /users`
  - **Projects & Membership:** `GET /projects` (search, status filter, pagination, computed progress & counts), `POST /projects`, `GET /projects/{project_id}`, `PUT /projects/{project_id}`, `DELETE /projects/{project_id}`, `POST /projects/{project_id}/members`, `DELETE /projects/{project_id}/members/{user_id}`
  - **User Stories:** `GET /projects/{project_id}/stories` (priority/status filters), `POST /projects/{project_id}/stories`, `GET /stories/{story_id}`, `PUT /stories/{story_id}`, `DELETE /stories/{story_id}`
  - **Tasks:** `GET /stories/{story_id}/tasks`, `POST /stories/{story_id}/tasks`, `GET /tasks` (cross-project filterable list for Kanban/search), `GET /tasks/{task_id}`, `PUT /tasks/{task_id}`, `PATCH /tasks/{task_id}/status`, `DELETE /tasks/{task_id}`
  - **My Tasks:** `GET /my-tasks` (strictly authenticated user's assigned tasks with status/priority/due filters)
  - **Dashboard:** `GET /dashboard/summary`, `GET /dashboard/project-progress`
  - **Notifications:** `GET /notifications`, `PATCH /notifications/{notification_id}/read`, `PATCH /notifications/read-all`
  - **Activity:** `GET /activity`
- Configure `backend/app/main.py` with CORS, structured exception handlers, lifespan DB init, `/health`, and Swagger UI at `http://localhost:8000/docs`.

### Phase 4: React Frontend, Design System, Layout & Pages
- Scaffold React + Vite + Tailwind CSS project in `frontend/`.
- Configure Tailwind tokens for the **KPIT-inspired Black, Green & White** palette (`#101010`, `#171717`, `#75C900`, `#FFFFFF`, `#F5F5F5`, `#E5E5E5`, `#737373`, `#16A34A`, `#F59E0B`, `#DC2626`).
- Build reusable UI primitives (`components/common/`): `Button` (Primary green/black, Secondary white/black-border, Destructive red, Disabled grey), `Card`, `Badge`, `Modal`, `ConfirmDialog`, `Input`, `Select`, `Textarea`, `EmptyState`, `LoadingSpinner`, `ProgressBar`, `BrandLogo` (custom SprintFlow mark—no official KPIT logo).
- Build `layouts/AppLayout.jsx`:
  - Black sidebar (`#101010`) with white text/icons, `#75C900` active indicator, SprintFlow logo, and all 7 links (Dashboard, Projects, My Tasks, Kanban Board, Notifications, Activity Log, Settings) + responsive mobile drawer.
  - Top navigation bar with dynamic page title, global search bar, notification bell with live unread count badge, user profile indicator, and logout button.
- Build `AuthContext`, `ToastContext`, `ProtectedRoute`, and all page views (`Login`, `Register`, `Dashboard`, `Projects`, `ProjectDetails`, `MyTasks`, `KanbanBoard`, `Notifications`, `ActivityLog`, `Settings`).

### Phase 5: Frontend–Backend Integration
- Build centralized Axios client (`frontend/src/services/api.js`) and modular API service modules (`auth.js`, `projects.js`, `stories.js`, `tasks.js`, `notifications.js`, `activity.js`, `dashboard.js`).
- Connect Login, Register, Logout, Settings (profile & password update), Projects CRUD + Search/Filter + Member Management, Project Details (`Project → User Story → Task` nested workflow), Story CRUD, Task CRUD, and TopNav global search to live FastAPI endpoints.
- Implement form validation, loading indicators, error banners, delete confirmation dialogs, and toast notifications.

### Phase 6: Kanban Board, My Tasks & Dashboard Analytics
- **Kanban Board (`KanbanBoard.jsx`):**
  - 4 columns (`To Do`, `In Progress`, `In Review`, `Done`), project/priority/assignee filters.
  - Cards display Task Title, User Story Name, Project Name, Assignee, Priority Badge, and Due Date (with overdue styling).
  - HTML5 Drag-and-Drop + quick status selector with optimistic UI update, `PATCH /tasks/{id}/status` persistence, toast feedback, and automatic UI rollback on failure.
- **My Tasks (`MyTasks.jsx`):**
  - Strictly shows authenticated user's assigned tasks with status/priority/overdue filters, upcoming deadline badges, overdue highlighting, detail inspection modal, and inline status update.
- **Dashboard (`Dashboard.jsx`):**
  - 7 dynamic KPI cards (Total Projects, Active Projects, Completed Projects, Total User Stories, Total Tasks, Completed Tasks, Overdue Tasks).
  - 4 Recharts visualizations styled in the Black/Green/White palette:
    1. Tasks by Status (Bar Chart)
    2. Project Progress % (Horizontal Bar Chart)
    3. Completed vs Pending Tasks (Donut Chart)
    4. Task Priority Distribution (Bar Chart)
  - 6 live sections: Recent Projects, Recent Activity, Upcoming Deadlines, Overdue Tasks, Recently Updated Tasks, My Assigned Tasks.

### Phase 7: Asynchronous Background Reminder Workflow & Notifications
- Implement `backend/app/background/deadline_reminders.py`:
  - Triggered via FastAPI `BackgroundTasks` on task create, update, and status change (non-blocking).
  - Opens an independent SQLAlchemy session.
  - Evaluates task assignee, status (`!= Done`), and `due_date`:
    - Generates `overdue_task` notification if `due_date < today`.
    - Generates `upcoming_deadline` notification if `today <= due_date <= today + DEADLINE_REMINDER_DAYS`.
  - Enforces duplicate prevention via deterministic `dedup_key` + DB `UNIQUE(user_id, dedup_key)`.
  - Implements bounded retries (max 3 attempts with backoff) for retryable DB errors, catches and logs all exceptions gracefully without affecting main task API responses, and persists attempt/result metadata into `background_job_logs`.
- Task assignment (`task_assignment`) notifications created persistently when tasks are assigned or reassigned.
- Wire `Notifications.jsx` and TopNav notification badge to `GET /notifications`, `PATCH /notifications/{id}/read`, and `PATCH /notifications/read-all`.

### Phase 8: Activity Logging, Authorization Hardening & Security Audit
- Verify all 11 activity log events are recorded chronologically and scoped to accessible projects:
  - `project_created`, `project_updated`, `project_deleted`
  - `story_created`, `story_updated`, `story_deleted`
  - `task_created`, `task_updated`, `task_assigned`, `task_status_changed`, `task_completed`
- Wire `ActivityLog.jsx` with entity/project filtering and clean chronological timeline.
- Conduct full security pass: verify zero hardcoded secrets, zero sensitive fields in API responses or logs, strict project membership guards on all project/story/task endpoints, personal isolation on `/my-tasks` and `/notifications`, CORS configuration, and safe error handling.

### Phase 9: Automated Testing, Debugging & End-to-End Verification
- Write and run comprehensive Pytest + `TestClient` suite (`backend/app/tests/`):
  - `test_auth.py`: registration, duplicate email rejection, login, invalid credentials, expired/invalid token, protected route access.
  - `test_projects.py`: CRUD, search/status filter, member add/remove, dynamic progress calculation.
  - `test_stories.py`: CRUD under projects, invalid project rejection, priority/status filtering.
  - `test_tasks.py`: CRUD under stories, invalid story rejection, status patch, assignee/priority/due-date filtering, `/my-tasks` isolation.
  - `test_database_integrity.py`: `Project → Story → Task` FK enforcement, cascading delete preventing orphans, unique constraints.
  - `test_background_reminders.py`: upcoming & overdue reminder generation, SQLite persistence, duplicate prevention across repeated triggers, bounded retry on simulated transient DB failure, graceful non-blocking failure handling & `background_job_logs` verification.
  - `test_security.py`: unauthorized 401 checks, cross-project non-member 403 checks, notification isolation, Pydantic 422 validation checks.
- Build frontend (`npm run build`), verify backend + frontend startup, and run end-to-end verification against live APIs.

### Phase 10: Documentation & GitHub Submission Readiness
- Author accurate, implementation-matched documentation:
  - `README.md` (setup, env config, running backend & frontend, Swagger URL, structure, DB & background overview)
  - `docs/ARCHITECTURE.md` (aligned with final implemented codebase)
  - `docs/DATABASE.md` (tables, columns, PK/FK, indexes, ER diagram, cascading rules)
  - `docs/API_DOCUMENTATION.md` (every endpoint, method, auth, request/response/error examples)
  - `docs/DESIGN_DECISIONS.md` (stack rationale, SQLite rationale, schema & background tradeoffs, limitations)
  - `docs/SECURITY.md` (auth, hashing, authorization, validation, secrets, known limitations)
  - `docs/AI_USAGE.md` (honest summary of how AI assisted in planning, coding, debugging, and docs)
  - `docs/FUTURE_IMPROVEMENTS.md` (PostgreSQL, Celery/Redis queue, WebSockets/SSE, analytics, RBAC, CI/CD)
- Verify all 24 items in Section 24 Final Verification Checklist and confirm clean Git status ready for GitHub push.

---

## 4. Requirement Traceability Checklist

Every requirement from Sections 1–24 of the KPIT assignment specification is mapped below:

| Spec Section | Requirement | Planned Implementation Location | Verification Method |
|---|---|---|---|
| **1. Objective** | Hierarchical `Project → User Story → Task` CRUD & organization | `models/{project,user_story,task}.py`, `routers/{projects,stories,tasks}.py`, `ProjectDetails.jsx` | API tests + UI walkthrough |
| **2. Tech Stack** | React, Vite, JS, Tailwind, Router, Axios, Recharts; FastAPI, SQLAlchemy, Pydantic, SQLite, BackgroundTasks, Pytest | `frontend/package.json`, `backend/requirements.txt` | Dependency audit + build |
| **3. UI/UX & Brand** | KPIT-inspired Black (`#101010`), Green (`#75C900`), White (`#FFFFFF`); no navy/purple; no official KPIT logo | `frontend/tailwind.config.js`, `components/common/*`, `layouts/AppLayout.jsx` | Visual inspection |
| **4. Navigation** | 7 sidebar pages + top nav (title, search, notifications, profile, logout) + protected routes + states | `App.jsx`, `AppLayout.jsx`, `ProtectedRoute.jsx` | Route & UI check |
| **5. Auth & Users** | Register, Login, Logout, `/auth/me`, bcrypt hashing, JWT, expiry handling, team membership | `core/security.py`, `routers/auth.py`, `routers/users.py`, `AuthContext.jsx` | `test_auth.py` |
| **6. Dashboard** | 7 dynamic KPI cards, 4 Recharts charts, 6 live sections, zero hardcoded data | `services/dashboard_service.py`, `routers/dashboard.py`, `pages/Dashboard.jsx` | API & live UI check |
| **7. Projects** | Full fields, 4 statuses, CRUD, search/filter, progress %, members, delete confirm, details page | `services/project_service.py`, `routers/projects.py`, `Projects.jsx`, `ProjectDetails.jsx` | `test_projects.py` |
| **8. User Stories** | Full fields (incl. acceptance criteria, story points), 4 priorities, 4 statuses, CRUD, project validation | `services/story_service.py`, `routers/stories.py`, `components/stories/*` | `test_stories.py` |
| **9. Tasks** | Full fields (incl. est/actual hours), 4 statuses, 4 priorities, CRUD, multi-filters, SQLite persistence | `services/task_service.py`, `routers/tasks.py`, `components/tasks/*` | `test_tasks.py` |
| **10. Kanban** | 4 columns, rich cards, Drag-and-Drop + status API persistence + optimistic UI & error rollback | `pages/KanbanBoard.jsx`, `components/kanban/*`, `PATCH /tasks/{id}/status` | API test + UI drag/refresh check |
| **11. My Tasks** | Authenticated user's tasks only, filters, upcoming/overdue highlights, detail view, status update | `routers/my_tasks.py`, `pages/MyTasks.jsx` | `test_tasks.py` + `test_security.py` |
| **12. Notifications** | Persistent SQLite notifications (`upcoming_deadline`, `overdue_task`, `task_assignment`), unread count, mark read / read-all | `models/notification.py`, `routers/notifications.py`, `pages/Notifications.jsx` | `test_background_reminders.py` |
| **13. Background Workflow** | FastAPI `BackgroundTasks` deadline reminder, dedup, bounded retries, graceful failure handling, result logging, honest limitation docs | `background/deadline_reminders.py`, `models/background_job_log.py`, `docs/ARCHITECTURE.md`, `docs/DESIGN_DECISIONS.md` | `test_background_reminders.py` |
| **14. Activity Log** | All 11 tracked events, chronological feed, entity/project metadata | `models/activity_log.py`, `services/activity_service.py`, `routers/activity.py`, `pages/ActivityLog.jsx` | API tests across CRUD flows |
| **15. Database** | 7 core tables (+ `background_job_logs`), PK/FK/indexes/uniques, `PRAGMA foreign_keys=ON`, cascading deletes, ER diagram | `database.py`, `models/*.py`, `docs/DATABASE.md` | `test_database_integrity.py` |
| **16. REST API** | All required endpoints, HTTP codes, Pydantic validation, pagination, Swagger UI (`/docs`) | `routers/*.py`, `schemas/*.py`, `main.py` | Pytest + `/docs` verification |
| **17. Security** | Bcrypt, JWT, `.env` secrets, membership authz, ORM queries, CORS, sanitized errors/logs | `core/security.py`, `core/dependencies.py`, `core/config.py`, `docs/SECURITY.md` | `test_security.py` |
| **18. Frontend** | Modular React structure, Axios services, protected routes, responsive UI, form validation | `frontend/src/**` | `npm run build` + live verification |
| **19. Testing** | Pytest + `TestClient` covering Auth, Projects, Stories, Tasks, DB, Background, Security | `backend/app/tests/*.py` | `pytest -v` passing 100% |
| **20–21. Structure & Docs** | Modular repo + `README.md` + 7 `docs/*.md` files + `.env.example` + `.gitignore` | Root + `docs/` | File & accuracy audit |

---

## 5. Key Engineering Tradeoffs to Confirm Before Implementation

1. **Operational Table (`background_job_logs`):** Alongside the 7 required domain tables, adding an 8th lightweight operational table `background_job_logs` lets us persist background reminder processing results and retry counts in SQLite (directly fulfilling Section 13: *"Record processing results"* and *"Track processing attempts"*).
2. **Supporting Utility Endpoints:** In addition to the exact endpoints listed in Section 16, adding `GET /users` (safe team directory for assignment/member selection), `POST/DELETE /projects/{id}/members`, `GET /tasks` (cross-project filterable tasks for Kanban & search), `PATCH /notifications/read-all`, and `PUT /auth/me` + `PUT /auth/me/password` (for the Settings page) makes every UI feature 100% database-backed.
3. **Seed Script (Optional Demo Helper):** We will keep the main database clean by default (so empty states work out-of-the-box and tests stay isolated), and optionally provide a standalone CLI script `backend/seed_demo.py` if you want sample team data during your interview demo.

> **Status:** Phase 1 complete. Awaiting your review and approval of this plan before beginning **Phase 2 (Database Setup, SQLAlchemy Models & Relationships)**.
