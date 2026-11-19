"""Authentication and user account service."""

from typing import List

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.schemas.auth import (
    PasswordChangeRequest,
    TokenResponse,
    UserLoginRequest,
    UserProfileUpdateRequest,
    UserPublicResponse,
    UserRegisterRequest,
)


def register_user(db: Session, payload: UserRegisterRequest) -> User:
    """Create a new user account with securely hashed password."""
    existing = db.scalar(select(User).where(User.email == payload.email))
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists.",
        )

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        password_hash=hash_password(payload.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, payload: UserLoginRequest) -> TokenResponse:
    """Validate credentials and issue a signed JWT access token."""
    user = db.scalar(select(User).where(User.email == payload.email))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    settings = get_settings()
    token = create_access_token(user_id=user.id, email=user.email)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        user=UserPublicResponse.model_validate(user),
    )


def update_user_profile(
    db: Session,
    current_user: User,
    payload: UserProfileUpdateRequest,
) -> User:
    """Update the authenticated user's display name."""
    current_user.full_name = payload.full_name
    db.commit()
    db.refresh(current_user)
    return current_user


def change_user_password(
    db: Session,
    current_user: User,
    payload: PasswordChangeRequest,
) -> None:
    """Verify current password and update the stored bcrypt password hash."""
    if not verify_password(payload.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )
    current_user.password_hash = hash_password(payload.new_password)
    db.commit()


def list_team_users(db: Session) -> List[User]:
    """Return all registered team users ordered alphabetically by full name."""
    stmt = select(User).order_by(User.full_name.asc())
    return list(db.scalars(stmt).all())
