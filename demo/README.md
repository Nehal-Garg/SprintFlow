# SprintFlow — Demo Screen Recordings

## Demo Videos
- **Screen Recording with Narration:** [Watch Video (Google Drive)](https://drive.google.com/drive/folders/128TmAp3FdILMqFpqxCtmC2u2LDPnyF3H)
- **Screen Recording without Narration (Full Silent Walkthrough, 1440×900):** [Watch on Google Drive](https://drive.google.com/drive/folders/128TmAp3FdILMqFpqxCtmC2u2LDPnyF3H) · [Local Repo File (`sprintflow_walkthrough_silent.webm`)](sprintflow_walkthrough_silent.webm)

## What the Demo Covers (5–7 Minutes)
1. **Technology Stack & Architecture Overview**
2. **User Registration, Login, `bcrypt` & `PyJWT` Authentication**
3. **Live Recharts Dashboard Analytics** (7 KPI cards, 4 charts, 6 live sections)
4. **Core `Project → User Story → Task` Hierarchy** (Team Members, Task Filters, Project Deadlines)
5. **Kanban Board Drag-and-Drop** (Assignee filtering, `PATCH /tasks/{id}/status` persistence & rollback)
6. **My Tasks User Isolation** (Self-assigned tasks, Overdue & Due Soon highlights)
7. **Persistent Notifications & FastAPI `BackgroundTasks` Execution Audit** (Job Logs & Mark Read)
8. **Chronological Activity Log** (12 lifecycle events)
9. **Interactive Swagger UI** (`http://localhost:8000/docs`)
10. **Automated Pytest Suite** (`36 passed`)

*(Full narration script & technical interview Q&A available in [../docs/INTERVIEW_AND_DEMO_GUIDE.md](../docs/INTERVIEW_AND_DEMO_GUIDE.md).)*
