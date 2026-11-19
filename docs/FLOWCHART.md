# SprintFlow — System & Workflow Flowcharts

> High-resolution architecture, Agile work hierarchy (`Project → User Story → Task`), and asynchronous `FastAPI BackgroundTasks` flowcharts for SprintFlow.

---

## 1. Full-Stack System Architecture Flowchart

![Full-Stack System Architecture Flowchart](diagrams/01_architecture_flowchart.png)

---

## 2. Hierarchical Agile Workflow (`Project → User Story → Task`)

![Hierarchical Agile Workflow Flowchart](diagrams/02_hierarchy_workflow_flowchart.png)

---

## 3. Asynchronous Background Reminder Pipeline (`FastAPI BackgroundTasks`)

![Asynchronous Background Reminder Flowchart](diagrams/03_background_reminders_flowchart.png)

> **Architectural Tradeoff:** FastAPI `BackgroundTasks` runs in-process after the HTTP response; queued reminders do not survive server restarts. For production scale, migrate to **Celery / Dramatiq + Redis** with a periodic scheduler (see [FUTURE_IMPROVEMENTS.md](FUTURE_IMPROVEMENTS.md)).
