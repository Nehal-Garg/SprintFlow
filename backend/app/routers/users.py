"""Team user directory routes."""

from typing import List

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models import User
from app.schemas.auth import UserPublicResponse
from app.services import auth_service

router = APIRouter(prefix="/users", tags=["Users"])


@router.get(
    "",
    response_model=List[UserPublicResponse],
    status_code=status.HTTP_200_OK,
    summary="List registered team users (safe fields only)",
)
def list_users(
    db: Session = Depends(get_db),
    _current_user: User = Depends(get_current_user),
) -> List[UserPublicResponse]:
    users = auth_service.list_team_users(db)
    return [UserPublicResponse.model_validate(u) for u in users]
