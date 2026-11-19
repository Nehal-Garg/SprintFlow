# AI Usage Disclosure

In accordance with the KPIT assignment guidelines, this document provides a transparent summary of how AI engineering tools assisted during the development of SprintFlow.

## How AI Assisted
1. **Requirements Analysis & Planning:** Assisted in mapping all assignment requirements into a structured 10-phase roadmap, architecture diagram, and requirement traceability checklist (`implementation_plan.md` and `architecture.md`).
2. **Code Scaffolding & Implementation Assistance:** Assisted in generating modular FastAPI routers, SQLAlchemy 2.x ORM models, Pydantic v2 validation schemas, the FastAPI `BackgroundTasks` deadline reminder worker, and React + Tailwind CSS UI components.
3. **Testing & Debugging:** Assisted in writing comprehensive Pytest + `TestClient` suites (covering database cascades, deduplication, retry simulation, and authorization boundaries) and diagnosing environment-specific issues (such as SQLAlchemy expired-instance handling in raw SQL cascade tests and Windows asyncio loopback behavior during test execution).
4. **Documentation Drafting:** Assisted in structuring and cross-checking technical documentation (`README.md`, `docs/*.md`) against the implemented codebase.

## Human Ownership & Verification
- Every architectural decision, security boundary, tradeoff (such as `PRAGMA foreign_keys=ON`, owner vs. member authorization rules, and honest documentation of FastAPI `BackgroundTasks` limitations), and code module was reviewed, tested, and verified directly against live execution.
- All automated tests (`36/36` passing), production frontend builds, and end-to-end verification flows were executed directly to validate real behavior rather than assuming correctness.
- I understand the full codebase end-to-end and am prepared to explain, modify, and defend every component during the technical interview.
