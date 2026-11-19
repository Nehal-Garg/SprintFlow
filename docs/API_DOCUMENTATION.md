# SprintFlow — REST API Documentation

- **Base URL (local):** `http://localhost:8000`
- **Interactive Swagger UI:** `http://localhost:8000/docs`
- **OpenAPI Schema:** `http://localhost:8000/openapi.json`
- **Authentication:** Bearer JWT header on all private endpoints:
  ```http
  Authorization: Bearer <access_token>
  ```

---

## Common Error Responses

| Status | Meaning | Example Payload |
|---|---|---|
| `400 Bad Request` | Business rule violation (e.g., assignee not in project, removing last owner) | `{"detail": "Assigned user must be a member of the project."}` |
| `401 Unauthorized` | Missing, invalid, or expired JWT / wrong login credentials | `{"detail": "Authentication token has expired."}` |
| `403 Forbidden` | Authenticated user lacks membership or owner permission | `{"detail": "Only project owners can perform this action."}` |
| `404 Not Found` | Resource does not exist | `{"detail": "Project 99 not found."}` |
| `409 Conflict` | Duplicate email, duplicate member, or constraint conflict | `{"detail": "An account with this email address already exists."}` |
| `422 Unprocessable Entity` | Pydantic validation error or forbidden extra field (`id`, `created_by`, etc.) | `{"detail": "Validation failed.", "errors": [{"field": "body.password", "message": "..."}]}` |

---

## 1. System & Authentication

### `GET /health` *(Public)*
Returns `200 OK`: `{"status": "ok", "app": "SprintFlow"}`.

### `POST /auth/register` *(Public)*
Register a new team user.
- **Body:** `{"full_name": "Priya Nair", "email": "priya@team.dev", "password": "Password123"}`
- **Response (`201 Created`):**
  ```json
  {
    "id": 1,
    "full_name": "Priya Nair",
    "email": "priya@team.dev",
    "created_at": "2026-11-19T09:00:00Z",
    "updated_at": "2026-11-19T09:00:00Z"
  }
  ```

### `POST /auth/login` *(Public)*
Authenticate and receive a JWT access token.
- **Body:** `{"email": "priya@team.dev", "password": "Password123"}`
- **Response (`200 OK`):**
  ```json
  {
    "access_token": "<jwt>",
    "token_type": "bearer",
    "expires_in": 3600,
    "user": { "id": 1, "full_name": "Priya Nair", "email": "priya@team.dev", "created_at": "...", "updated_at": "..." }
  }
  ```

### `GET /auth/me` *(Auth Required)*
Returns the authenticated user's profile (`200 OK`, never exposes `password_hash`).

### `PUT /auth/me` *(Auth Required)*
Updates `full_name`. Body: `{"full_name": "Priya K. Nair"}`.

### `PUT /auth/me/password` *(Auth Required)*
Rotates password after verifying current password. Body: `{"current_password": "...", "new_password": "..."}`.

### `GET /users` *(Auth Required)*
Lists registered team users (safe public fields only) for project membership selection.

---

## 2. Projects & Membership

### `GET /projects` *(Auth Required)*
Lists projects where the authenticated user is a member, enriched with computed `progress`, `story_count`, `task_count`, `completed_task_count`, and `members`.
- **Query Params:** `search`, `status` (`Planning|Active|On Hold|Completed`), `skip` (default `0`), `limit` (default `50`).

### `POST /projects` *(Auth Required)*
Creates a project and enrolls the creator as `owner`.
- **Body:** `{"name": "E-Commerce Website", "description": "...", "start_date": "2026-11-01", "end_date": "2026-12-31", "status": "Active"}`
- **Response:** `201 Created` (`ProjectResponse`).

### `GET /projects/{project_id}` *(Project Member)*
Returns full project details, progress metrics, and members (`200 OK`).

### `PUT /projects/{project_id}` *(Project Member)*
Updates project metadata (`200 OK`). `id` and `created_by` cannot be modified.

### `DELETE /projects/{project_id}` *(Project Owner Only)*
Deletes the project and cascades all members, user stories, and tasks (`204 No Content`).

### `POST /projects/{project_id}/members` *(Project Owner Only)*
Adds an existing user to the project. Body: `{"user_id": 2, "role": "member"}` (`201 Created`).

### `DELETE /projects/{project_id}/members/{user_id}` *(Project Owner Only)*
Removes a member (blocks removal of the sole remaining owner) and clears their project assignments (`204 No Content`).

---

## 3. User Stories

### `GET /projects/{project_id}/stories` *(Project Member)*
Lists user stories under a project.
- **Query Params:** `priority` (`Low|Medium|High|Critical`), `status` (`Backlog|To Do|In Progress|Done`), `search`, `skip`, `limit`.

### `POST /projects/{project_id}/stories` *(Project Member)*
Creates a user story inside an existing project. Validates `assigned_to` belongs to the project.
- **Body:** `{"title": "User Authentication", "description": "...", "acceptance_criteria": "...", "priority": "High", "status": "In Progress", "story_points": 5, "assigned_to": 1, "due_date": "2026-12-01"}`
- **Response:** `201 Created` (`UserStoryResponse`).

### `GET /stories/{story_id}` *(Project Member)*
Returns story details with task counts (`200 OK`).

### `PUT /stories/{story_id}` *(Project Member)*
Updates a user story (`project_id` is immutable) (`200 OK`).

### `DELETE /stories/{story_id}` *(Project Member)*
Deletes a user story and cascades its child tasks (`204 No Content`).

---

## 4. Tasks & My Tasks

### `GET /stories/{story_id}/tasks` *(Project Member)*
Lists tasks under a specific user story.
- **Query Params:** `status`, `priority`, `assignee_id`, `due_before`, `due_after`, `overdue_only`, `skip`, `limit`.

### `POST /stories/{story_id}/tasks` *(Project Member)*
Creates a task under an existing user story, persists a `task_assignment` notification if assigned, and schedules the background deadline reminder workflow via FastAPI `BackgroundTasks`.
- **Body:** `{"title": "Develop registration API", "description": "...", "assignee_id": 2, "priority": "High", "status": "To Do", "start_date": "2026-11-19", "due_date": "2026-11-21", "estimated_hours": 4.0, "actual_hours": 0.0}`
- **Response:** `201 Created` (`TaskResponse`).

### `GET /tasks` *(Auth Required)*
Lists tasks across projects accessible to the authenticated user (powers the Kanban Board).
- **Query Params:** `project_id`, `status`, `priority`, `assignee_id`, `search`, `due_before`, `due_after`, `overdue_only`, `skip`, `limit`.

### `GET /tasks/{task_id}` *(Project Member)*
Returns task details enriched with `project_name`, `user_story_title`, `assignee_name`, and `is_overdue` (`200 OK`).

### `PUT /tasks/{task_id}` *(Project Member)*
Updates task details (`user_story_id` is immutable), records assignment notification on reassignment, and triggers the background deadline reminder workflow (`200 OK`).

### `PATCH /tasks/{task_id}/status` *(Project Member)*
Transitions task status (`To Do | In Progress | In Review | Done`), logs status change & completion activity, and re-evaluates deadline reminders asynchronously (`200 OK`).
- **Body:** `{"status": "Done"}`

### `DELETE /tasks/{task_id}` *(Project Member)*
Deletes a task (`204 No Content`).

### `GET /my-tasks` *(Auth Required)*
Strictly returns tasks assigned to the authenticated user (`assignee_id == current_user.id`) within their accessible projects.
- **Query Params:** `status`, `priority`, `overdue_only`, `skip`, `limit`.

---

## 5. Notifications, Activity Log & Dashboard

### `GET /notifications` *(Auth Required)*
Returns persistent notifications strictly belonging to the authenticated user along with `unread_count`.
- **Query Params:** `unread_only`, `notification_type` (`upcoming_deadline|overdue_task|task_assignment`), `skip`, `limit`.

### `PATCH /notifications/{notification_id}/read` *(Notification Owner Only)*
Marks a single notification as read (`200 OK`; `403 Forbidden` if owned by another user).

### `PATCH /notifications/read-all` *(Auth Required)*
Marks all unread notifications for the authenticated user as read (`200 OK`).

### `GET /notifications/job-logs` *(Auth Required)*
Returns recent `background_job_logs` records for tasks in the user's accessible projects (`200 OK`).

### `GET /activity` *(Auth Required)*
Returns chronological activity logs scoped to the user's accessible projects.
- **Query Params:** `project_id`, `entity_type` (`project|user_story|task`), `action`, `skip`, `limit`.

### `GET /dashboard/summary` *(Auth Required)*
Returns all live KPIs, status & priority distributions, project progress, recent projects, recent activity, upcoming deadlines (7 days), overdue tasks, recently updated tasks, and `my_assigned_tasks` (`200 OK`).

### `GET /dashboard/project-progress` *(Auth Required)*
Returns live task completion percentages for every accessible project (`200 OK`).
