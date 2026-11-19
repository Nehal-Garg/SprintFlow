"""Authentication and user profile Pydantic schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


def _validate_password_strength(value: str) -> str:
    if len(value) < 8:
        raise ValueError("Password must be at least 8 characters long.")
    if len(value) > 72:
        raise ValueError("Password must not exceed 72 characters.")
    if not any(ch.isalpha() for ch in value) or not any(ch.isdigit() for ch in value):
        raise ValueError("Password must contain at least one letter and one number.")
    return value


class UserRegisterRequest(BaseModel):
    """Payload for new user registration."""

    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(..., min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=72)

    @field_validator("full_name")
    @classmethod
    def strip_full_name(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise ValueError("Full name must contain at least 2 non-whitespace characters.")
        return cleaned

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()

    @field_validator("password")
    @classmethod
    def check_password_strength(cls, value: str) -> str:
        return _validate_password_strength(value)


class UserLoginRequest(BaseModel):
    """Payload for email/password login."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(..., min_length=1, max_length=72)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> str:
        return str(value).strip().lower()


class UserProfileUpdateRequest(BaseModel):
    """Payload for updating the current user's profile."""

    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(..., min_length=2, max_length=120)

    @field_validator("full_name")
    @classmethod
    def strip_full_name(cls, value: str) -> str:
        cleaned = value.strip()
        if len(cleaned) < 2:
            raise ValueError("Full name must contain at least 2 non-whitespace characters.")
        return cleaned


class PasswordChangeRequest(BaseModel):
    """Payload for changing the current user's password."""

    model_config = ConfigDict(extra="forbid")

    current_password: str = Field(..., min_length=1, max_length=72)
    new_password: str = Field(..., min_length=8, max_length=72)

    @field_validator("new_password")
    @classmethod
    def check_new_password(cls, value: str) -> str:
        return _validate_password_strength(value)


class UserPublicResponse(BaseModel):
    """Safe user representation that never exposes password hashes."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    full_name: str
    email: str
    created_at: datetime
    updated_at: datetime


class TokenResponse(BaseModel):
    """JWT access token response returned on login."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserPublicResponse
