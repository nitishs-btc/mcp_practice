"""Shared models for the server's public response types."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class RedactionResponse(BaseModel):
    """Structured output returned by the redact_text tool."""

    redacted_text: str = Field(description="Redacted text returned by Philter.")


class HealthResponse(BaseModel):
    """Server and provider health information."""

    status: str
    provider: str
    details: dict[str, Any] = Field(default_factory=dict)
