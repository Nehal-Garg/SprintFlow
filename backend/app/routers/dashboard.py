"""Dynamic dashboard analytics routes."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.dashboard import DashboardSummaryResponse, ProjectProgressResponse
from app.services import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get live dashboard KPIs, charts, deadlines, and recent work",
)
def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DashboardSummaryResponse:
    return dashboard_service.get_dashboard_summary(db, current_user)


@router.get(
    "/project-progress",
    response_model=ProjectProgressResponse,
    status_code=status.HTTP_200_OK,
    summary="Get real-time completion percentages for every accessible project",
)
def get_project_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectProgressResponse:
    return dashboard_service.get_project_progress(db, current_user)
