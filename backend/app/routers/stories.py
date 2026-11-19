"""User Story CRUD routes under projects and direct story endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.user_story import (
    StoryPriority,
    StoryStatus,
    UserStoryCreateRequest,
    UserStoryListResponse,
    UserStoryResponse,
    UserStoryUpdateRequest,
)
from app.services import story_service

router = APIRouter(tags=["User Stories"])


@router.get(
    "/projects/{project_id}/stories",
    response_model=UserStoryListResponse,
    status_code=status.HTTP_200_OK,
    summary="List user stories belonging to a project",
)
def list_project_stories(
    project_id: int,
    priority: Optional[StoryPriority] = Query(default=None),
    status_filter: Optional[StoryStatus] = Query(default=None, alias="status"),
    search: Optional[str] = Query(default=None, max_length=200),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserStoryListResponse:
    return story_service.list_project_stories(
        db,
        project_id,
        current_user,
        priority=priority,
        status_filter=status_filter,
        search=search,
        skip=skip,
        limit=limit,
    )


@router.post(
    "/projects/{project_id}/stories",
    response_model=UserStoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user story inside an existing project",
)
def create_story(
    project_id: int,
    payload: UserStoryCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserStoryResponse:
    return story_service.create_story(db, project_id, payload, current_user)


@router.get(
    "/stories/{story_id}",
    response_model=UserStoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get user story details",
)
def get_story(
    story_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserStoryResponse:
    return story_service.get_story(db, story_id, current_user)


@router.put(
    "/stories/{story_id}",
    response_model=UserStoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a user story",
)
def update_story(
    story_id: int,
    payload: UserStoryUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserStoryResponse:
    return story_service.update_story(db, story_id, payload, current_user)


@router.delete(
    "/stories/{story_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a user story and cascade its tasks",
)
def delete_story(
    story_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    story_service.delete_story(db, story_id, current_user)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
