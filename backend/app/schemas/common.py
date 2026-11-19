"""Shared response schemas."""

from pydantic import BaseModel


class MessageResponse(BaseModel):
    """Standard informational message payload."""

    message: str


class HealthResponse(BaseModel):
    """Health check payload."""

    status: str
    app: str
