# SprintFlow — Testing & Verification Report

## 1. Automated Backend Test Suite (`pytest`)

All backend tests run against fresh, isolated per-test SQLite databases (`tmp_path`) with `PRAGMA foreign_keys=ON` and FastAPI dependency overrides for both `get_db` and `get_session_factory`, ensuring zero contamination of `backend/sprintflow.db`.

### Execution Command
```powershell
backend\.venv\Scripts\python.exe -m pytest backend\app\tests -c backend\pytest.ini --rootdir=backend
```

### Coverage Summary (`36 passed, 0 failed`)

| Test Module | Tests | What Is Verified |
|---|---|---|
| `test_database_integrity.py` | 13 | Table creation (all 8 tables), `PRAGMA foreign_keys=ON`, `Project → Story → Task` bidirectional ORM traversal, orphan prevention (`IntegrityError`), SQL & ORM cascading deletes, audit `SET NULL` preservation, unique constraints (`email`, `project_members`, `notifications(user_id, dedup_key)`), `CHECK` constraints, `background_job_logs`, and schema indexes/FKs. |
| `test_auth.py` | 7 | Registration with bcrypt hashing, `password_hash` non-exposure, duplicate email (`409`) & weak password (`422`) rejection, login + `/auth/me`, invalid credentials (`401`), missing/tampered/expired JWT rejection (`401`), profile & password rotation, Swagger `/docs` & `/openapi.json` availability. |
| `test_projects.py` | 3 | Project CRUD, search & status filters, dynamic progress, owner vs. member vs. outsider authorization matrix (`403`), last-owner deletion protection (`400`), date sanity & mass-assignment rejection (`422`). |
| `test_stories.py` | 2 | Story CRUD under projects, priority/status filtering, missing project `404`, non-member assignee rejection (`400`), outsider `403`, immutable `project_id` (`422`). |
| `test_tasks.py` | 2 | Full `Project → User Story → Task` lifecycle, `PATCH /tasks/{id}/status` + live progress recalculation, `/my-tasks` strict user isolation, cascade deletion via API, invalid story `404`, non-member `403`, immutable `user_story_id`. |
| `test_background_reminders.py` | 6 | FastAPI `BackgroundTasks` upcoming deadline & overdue notification generation, task assignment notifications, duplicate prevention across repeated edits, `Done` task skip behavior, bounded retry recovery after simulated transient `OperationalError`, graceful failure logging on exhausted retries, notification read / read-all & cross-user `403` isolation. |
| `test_dashboard_activity_security.py` | 3 | Dynamic dashboard KPIs & project progress scoped by membership, all 11 required chronological activity log events, cross-project activity isolation, `401` across all private endpoints, and SQL injection string safety. |

---

## 2. Frontend Production Build Verification

### Execution Command
```powershell
npm --prefix frontend run build
```

### Result
- **Status:** Passed cleanly (`vite build`, 2086 modules transformed, 0 errors, 0 warnings).
- **Optimized Output Chunks:** `index.html`, Tailwind CSS bundle (`26.52 kB`), `react-vendor`, `charts` (Recharts), `icons`, and application bundle.

---

## 3. End-to-End Live Workflow Verification

Executed against live running **Uvicorn** (`FastAPI`) and **Vite Preview** (`React production build`) servers using a fresh SQLite database, confirming all 12 steps pass:
1. User registration (Owner & Member)
2. JWT login & `/auth/me` verification
3. Project creation
4. Project member addition
5. User story creation under project
6. Multi-task creation with upcoming & overdue deadlines
7. Task assignment to project members
8. Kanban status update (`PATCH /tasks/{id}/status`)
9. Persisted Kanban task retrieval (`GET /tasks`)
10. Dynamic Dashboard KPI & 50.0% project progress calculation
11. Background deadline notifications (`upcoming_deadline`, `overdue_task`), assignment alerts, and `background_job_logs` persistence
12. Chronological Activity Log verification + Swagger `/docs` & Frontend HTTP 200 delivery
