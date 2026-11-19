"""Project CRUD and project membership routes."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectListResponse,
    ProjectMemberAddRequest,
    ProjectMemberResponse,
    ProjectResponse,
    ProjectStatus,
    ProjectUpdateRequest,
)
from app.services import project_service

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.get(
    "",
    response_model=ProjectListResponse,
    status_code=status.HTTP_200_OK,
    summary="List projects accessible to the authenticated user",
)
def list_projects(
    search: Optional[str] = Query(default=None, max_length=150),
    status_filter: Optional[ProjectStatus] = Query(default=None, alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectListResponse:
    return project_service.list_projects(
        db,
        current_user,
        search=search,
        status_filter=status_filter,
        skip=skip,
        limit=limit,
    )


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project and enroll the creator as owner",
)
def create_project(
    payload: ProjectCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    return project_service.create_project(db, payload, current_user)


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Get project details (project members only)",
)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    return project_service.get_project(db, project_id, current_user)


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a project (project members only)",
)
def update_project(
    project_id: int,
    payload: ProjectUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectResponse:
    return project_service.update_project(db, project_id, payload, current_user)


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project and cascade its stories and tasks (project owners only)",
)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    project_service.delete_project(db, project_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/{project_id}/members",
    response_model=ProjectMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add a user to a project (project owners only)",
)
def add_member(
    project_id: int,
    payload: ProjectMemberAddRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectMemberResponse:
    return project_service.add_project_member(db, project_id, payload, current_user)


@router.delete(
    "/{project_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a member from a project (project owners only)",
)
def remove_member(
    project_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    project_service.remove_project_member(db, project_id, user_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
