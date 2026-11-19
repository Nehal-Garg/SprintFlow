"""Environment-driven application configuration for SprintFlow."""

import os
import secrets
from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE_PATH = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables or backend/.env."""

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = Field(default="SprintFlow")
    environment: str = Field(default="development")

    database_url: str = Field(
        default=f"sqlite:///{(BACKEND_DIR / 'sprintflow.db').as_posix()}"
    )

    secret_key: str = Field(default_factory=lambda: secrets.token_hex(32))
    algorithm: str = Field(default="HS256")
    access_token_expire_minutes: int = Field(default=60, ge=1)

    cors_origins: str = Field(
        default="http://localhost:5173,http://127.0.0.1:5173"
    )

    deadline_reminder_days: int = Field(default=2, ge=0)
    background_max_retries: int = Field(default=3, ge=1, le=10)
    background_retry_base_delay_seconds: float = Field(default=0.2, ge=0.0, le=5.0)

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        env = os.getenv("ENVIRONMENT", "development").lower()
        if env == "production" and (
            not value or value.startswith("replace-with-") or len(value) < 32
        ):
            raise ValueError(
                "SECRET_KEY must be explicitly configured with at least 32 characters in production."
            )
        return value

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()
