"""Pydantic request and response schemas package."""

from app.schemas.activity import ActivityLogListResponse, ActivityLogResponse
from app.schemas.auth import (
    PasswordChangeRequest,
    TokenResponse,
    UserLoginRequest,
    UserProfileUpdateRequest,
    UserPublicResponse,
    UserRegisterRequest,
)
from app.schemas.common import HealthResponse, MessageResponse
from app.schemas.dashboard import (
    DashboardSummaryResponse,
    PriorityCountItem,
    ProjectProgressItem,
    ProjectProgressResponse,
    StatusCountItem,
)
from app.schemas.notification import (
    BackgroundJobLogResponse,
    NotificationListResponse,
    NotificationReadAllResponse,
    NotificationResponse,
)
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectListResponse,
    ProjectMemberAddRequest,
    ProjectMemberResponse,
    ProjectResponse,
    ProjectUpdateRequest,
)
from app.schemas.task import (
    TaskCreateRequest,
    TaskListResponse,
    TaskResponse,
    TaskStatusUpdateRequest,
    TaskUpdateRequest,
)
from app.schemas.user_story import (
    UserStoryCreateRequest,
    UserStoryListResponse,
    UserStoryResponse,
    UserStoryUpdateRequest,
)

__all__ = [
    "HealthResponse",
    "MessageResponse",
    "UserRegisterRequest",
    "UserLoginRequest",
    "UserProfileUpdateRequest",
    "PasswordChangeRequest",
    "UserPublicResponse",
    "TokenResponse",
    "ProjectCreateRequest",
    "ProjectUpdateRequest",
    "ProjectMemberAddRequest",
    "ProjectMemberResponse",
    "ProjectResponse",
    "ProjectListResponse",
    "UserStoryCreateRequest",
    "UserStoryUpdateRequest",
    "UserStoryResponse",
    "UserStoryListResponse",
    "TaskCreateRequest",
    "TaskUpdateRequest",
    "TaskStatusUpdateRequest",
    "TaskResponse",
    "TaskListResponse",
    "NotificationResponse",
    "NotificationListResponse",
    "NotificationReadAllResponse",
    "BackgroundJobLogResponse",
    "ActivityLogResponse",
    "ActivityLogListResponse",
    "StatusCountItem",
    "PriorityCountItem",
    "ProjectProgressItem",
    "ProjectProgressResponse",
    "DashboardSummaryResponse",
]
