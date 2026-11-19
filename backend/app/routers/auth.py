"""Authentication and current user profile routes."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.auth import (
    PasswordChangeRequest,
    TokenResponse,
    UserLoginRequest,
    UserProfileUpdateRequest,
    UserPublicResponse,
    UserRegisterRequest,
)
from app.schemas.common import MessageResponse
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserPublicResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
def register(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
) -> UserPublicResponse:
    user = auth_service.register_user(db, payload)
    return UserPublicResponse.model_validate(user)


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and issue JWT access token",
)
def login(
    payload: UserLoginRequest,
    db: Session = Depends(get_db),
) -> TokenResponse:
    return auth_service.authenticate_user(db, payload)


@router.get(
    "/me",
    response_model=UserPublicResponse,
    status_code=status.HTTP_200_OK,
    summary="Get the authenticated user's profile",
)
def get_me(current_user: User = Depends(get_current_user)) -> UserPublicResponse:
    return UserPublicResponse.model_validate(current_user)


@router.put(
    "/me",
    response_model=UserPublicResponse,
    status_code=status.HTTP_200_OK,
    summary="Update the authenticated user's display name",
)
def update_me(
    payload: UserProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UserPublicResponse:
    updated = auth_service.update_user_profile(db, current_user, payload)
    return UserPublicResponse.model_validate(updated)


@router.put(
    "/me/password",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
    summary="Change the authenticated user's password",
)
def change_password(
    payload: PasswordChangeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    auth_service.change_user_password(db, current_user, payload)
    return MessageResponse(message="Password updated successfully.")
