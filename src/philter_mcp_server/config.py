"""Application configuration."""

from __future__ import annotations

from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables and .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    provider: Literal["rule-based", "philter-api"] = Field(
        default="rule-based",
        alias="PHILTER_MCP_PROVIDER",
    )
    host: str = Field(default="127.0.0.1", alias="PHILTER_MCP_HOST")
    port: int = Field(default=8001, alias="PHILTER_MCP_PORT")
    log_level: str = Field(default="INFO", alias="PHILTER_MCP_LOG_LEVEL")
    philter_api_url: str = Field(
        default="http://localhost:8080/api/filter",
        alias="PHILTER_API_URL",
    )
    philter_api_timeout_seconds: float = Field(
        default=10.0,
        alias="PHILTER_API_TIMEOUT_SECONDS",
    )
    philter_api_verify_ssl: bool = Field(
        default=False,
        alias="PHILTER_API_VERIFY_SSL",
    )


settings = Settings()
