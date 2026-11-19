# SprintFlow — Security Architecture & Known Limitations

## 1. Authentication & Password Security

- **Password Hashing:** All user passwords are salted and hashed with `bcrypt` (`12` work-factor rounds) in `backend/app/core/security.py`. Plain-text passwords are never stored, logged, or echoed.
- **Constant-Time Verification:** Login and password changes verify hashes using `bcrypt.checkpw`.
- **Password Policy:** Registration and password rotation enforce minimum length (8 characters, max 72 bytes per bcrypt spec) and require at least one letter and one digit.
- **JWT Authentication:** Access tokens are signed with `HS256` via `PyJWT`, include `sub`, `email`, `iat`, and `exp` claims, and are validated strictly on every private route by `get_current_user`. Expired or tampered tokens immediately return `401 Unauthorized`.

---

## 2. Authorization & Access Control

| Resource / Action | Enforced Server-Side Check |
|---|---|
| `GET /projects`, `GET /tasks`, `GET /dashboard/*`, `GET /activity` | Filtered strictly to project IDs where `current_user` is in `project_members` |
| `GET /projects/{id}`, `PUT /projects/{id}` | `require_project_member` (`403` for outsiders, `404` if missing) |
| `DELETE /projects/{id}`, `POST/DELETE /projects/{id}/members` | `require_project_owner` (`403` for non-owner members and outsiders) |
| Stories & Tasks CRUD | `require_story_access` / `require_task_access` verifying parent project membership (`403` for outsiders) |
| Story & Task Assignments | `validate_project_assignee` ensuring assignee belongs to the parent project (`400` otherwise) |
| `GET /my-tasks` | Strictly filters `Task.assignee_id == current_user.id` within accessible projects |
| `GET /notifications`, `PATCH /notifications/{id}/read` | Strictly checks `Notification.user_id == current_user.id` (`403` on cross-user attempt) |

Frontend controls (such as hiding Delete Project and Member Management for non-owners) mirror backend permissions, while the backend remains the authoritative enforcement boundary.

---

## 3. Input Validation, Database & Error Security

- **Strict Request Validation:** Pydantic v2 schemas enforce types, length limits, enum literals, date ordering (`end_date >= start_date`, `due_date >= start_date`), and `ConfigDict(extra="forbid")` to defeat mass-assignment attacks (`created_by`, `project_id`, `user_story_id`, `id`).
- **SQL Injection Prevention:** All database reads and writes go through SQLAlchemy ORM parameterized statements (tested with SQLi strings in `test_dashboard_activity_security.py`).
- **No Credential Leakage:** `UserPublicResponse` never includes `password_hash`. Centralized exception handlers in `backend/app/main.py` sanitize database `IntegrityError` and unhandled `500` responses so raw SQL queries or stack traces are never exposed to clients.
- **Secrets Management:** `SECRET_KEY`, `DATABASE_URL`, and `CORS_ORIGINS` are loaded via `pydantic-settings` from `backend/.env` (gitignored). Zero secret keys or credentials are hardcoded in source files; production mode rejects weak or placeholder `SECRET_KEY` values.
- **CORS:** Restricted explicitly to origins listed in `CORS_ORIGINS` (default `http://localhost:5173`, `http://127.0.0.1:5173`).

---

## 4. Known Security Limitations & Production Hardening Path

1. **JWT Storage in `localStorage`:** The SPA stores the Bearer JWT in `localStorage` for simplicity during local development. While React escapes rendered text by default to mitigate XSS, a production deployment should move tokens to `HttpOnly; Secure; SameSite=Lax` cookies with CSRF protection.
2. **No Refresh Token Rotation or Server-Side Revocation List:** Access tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES` (default 60 min); logout removes the token client-side. Production deployments should add short-lived access tokens + revocable refresh tokens.
3. **No Rate Limiting:** Login and registration endpoints do not yet enforce IP/account throttling (e.g., `slowapi` / API gateway rate limits) against brute-force attempts.
4. **Local HTTP vs. HTTPS:** Local development runs over HTTP. Production deployment must terminate TLS (HTTPS) and set strict security headers (`HSTS`, `CSP`, `X-Frame-Options`).
5. **Global Team Directory (`GET /users`):** Designed for a trusted 3–10 person single-team workspace so project owners can add registered teammates by name/email. Multi-tenant SaaS deployments would isolate users by organization/tenant ID and use email invitations.
