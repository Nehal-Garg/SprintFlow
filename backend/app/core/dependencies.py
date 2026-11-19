"""FastAPI dependencies for database sessions, JWT authentication, and authorization."""

from typing import Generator, List, Optional, Tuple

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.security import decode_access_token
from app.database import SessionLocal
from app.models import Project, ProjectMember, Task, User, UserStory

bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    """Provide a transactional SQLAlchemy database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session_factory():
    """Return the active sessionmaker for background tasks (overridable in tests)."""
    return SessionLocal


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Authenticate the caller via Bearer JWT and return the active User record."""
    if credentials is None or credentials.scheme.lower() != "bearer" or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    subject = payload.get("sub")
    try:
        user_id = int(subject)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token subject.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user account no longer exists.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_accessible_project_ids(db: Session, user_id: int) -> List[int]:
    """Return all project IDs where the specified user is a member."""
    stmt = select(ProjectMember.project_id).where(ProjectMember.user_id == user_id)
    return list(db.scalars(stmt).all())


def get_project_membership(
    db: Session,
    project_id: int,
    user_id: int,
) -> Optional[ProjectMember]:
    """Look up a user's membership record in a specific project."""
    stmt = select(ProjectMember).where(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id,
    )
    return db.scalar(stmt)


def require_project_member(
    db: Session,
    project_id: int,
    current_user: User,
) -> Tuple[Project, ProjectMember]:
    """Verify the project exists and the current user is an authorized member."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found.",
        )

    membership = get_project_membership(db, project_id, current_user.id)
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this project.",
        )
    return project, membership


def require_project_owner(
    db: Session,
    project_id: int,
    current_user: User,
) -> Tuple[Project, ProjectMember]:
    """Verify the current user is a project owner for privileged project actions."""
    project, membership = require_project_member(db, project_id, current_user)
    if membership.role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only project owners can perform this action.",
        )
    return project, membership


def require_story_access(
    db: Session,
    story_id: int,
    current_user: User,
) -> Tuple[UserStory, ProjectMember]:
    """Verify the user story exists and the current user belongs to its parent project."""
    stmt = (
        select(UserStory)
        .options(joinedload(UserStory.project), joinedload(UserStory.assignee))
        .where(UserStory.id == story_id)
    )
    story = db.scalar(stmt)
    if story is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User story {story_id} not found.",
        )

    membership = get_project_membership(db, story.project_id, current_user.id)
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this user story.",
        )
    return story, membership


def require_task_access(
    db: Session,
    task_id: int,
    current_user: User,
) -> Tuple[Task, ProjectMember]:
    """Verify the task exists and the current user belongs to its parent project."""
    stmt = (
        select(Task)
        .options(
            joinedload(Task.user_story).joinedload(UserStory.project),
            joinedload(Task.assignee),
        )
        .where(Task.id == task_id)
    )
    task = db.scalar(stmt)
    if task is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found.",
        )

    membership = get_project_membership(db, task.user_story.project_id, current_user.id)
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this task.",
        )
    return task, membership


def validate_project_assignee(
    db: Session,
    project_id: int,
    assignee_id: Optional[int],
) -> Optional[User]:
    """Ensure an assigned user exists and is a member of the target project."""
    if assignee_id is None:
        return None

    user = db.get(User, assignee_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Assigned user {assignee_id} does not exist.",
        )

    membership = get_project_membership(db, project_id, assignee_id)
    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Assigned user must be a member of the project.",
        )
    return user
