"""Shared models for tool inputs and outputs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EntitySpan(BaseModel):
    """A detected PHI/PII entity span."""

    entity_type: str = Field(description="Normalized entity type, for example name or email.")
    start: int = Field(ge=0, description="Start character offset, inclusive.")
    end: int = Field(ge=0, description="End character offset, exclusive.")
    confidence: float = Field(ge=0.0, le=1.0, description="Detection confidence.")


class RedactionResponse(BaseModel):
    """Structured output returned by the redact_text tool."""

    entities: list[EntitySpan]


class HealthResponse(BaseModel):
    """Server and provider health information."""

    status: str
    provider: str
    details: dict[str, Any] = Field(default_factory=dict)
