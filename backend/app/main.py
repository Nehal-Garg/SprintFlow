"""FastAPI application factory, middleware, exception handlers, and router mounting."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.database import init_db
from app.routers import (
    activity,
    auth,
    dashboard,
    my_tasks,
    notifications,
    projects,
    stories,
    tasks,
    users,
)
from app.schemas.common import HealthResponse

logger = logging.getLogger("sprintflow")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialize SQLite tables cleanly when the application starts."""
    init_db()
    yield


def create_app() -> FastAPI:
    """Create and configure the SprintFlow FastAPI application instance."""
    settings = get_settings()

    application = FastAPI(
        title="SprintFlow API",
        description=(
            "Agile Project Management REST API for small development teams "
            "implementing hierarchical Project -> User Story -> Task tracking."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        errors = [
            {
                "field": ".".join(str(loc) for loc in err.get("loc", [])),
                "message": err.get("msg", "Invalid input"),
            }
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": "Validation failed.", "errors": errors},
        )

    @application.exception_handler(IntegrityError)
    async def integrity_exception_handler(
        _request: Request,
        _exc: IntegrityError,
    ) -> JSONResponse:
        # Never expose raw SQL statements or internal constraint details to clients
        logger.warning("Database integrity violation encountered during request.")
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": "The requested operation conflicts with existing data or relational constraints."
            },
        )

    @application.exception_handler(Exception)
    async def unhandled_exception_handler(
        _request: Request,
        exc: Exception,
    ) -> JSONResponse:
        logger.exception("Unhandled server exception: %s", type(exc).__name__)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected internal server error occurred."},
        )

    @application.get(
        "/health",
        response_model=HealthResponse,
        tags=["System"],
        summary="Health check endpoint",
    )
    def health_check() -> HealthResponse:
        return HealthResponse(status="ok", app=settings.app_name)

    application.include_router(auth.router)
    application.include_router(users.router)
    application.include_router(projects.router)
    application.include_router(stories.router)
    application.include_router(tasks.router)
    application.include_router(my_tasks.router)
    application.include_router(notifications.router)
    application.include_router(activity.router)
    application.include_router(dashboard.router)

    return application


app = create_app()
