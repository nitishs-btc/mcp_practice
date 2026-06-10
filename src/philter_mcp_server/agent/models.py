"""Request and response models for the public agent API."""

from __future__ import annotations

from pydantic import BaseModel, Field

from philter_mcp_server.models import EntitySpan


class RedactionRequest(BaseModel):
    """Input payload accepted by the public API."""

    text: str = Field(description="Plain text to scan for PHI/PII spans.")


class RedactionResult(BaseModel):
    """Response payload returned by the public API."""

    entities: list[EntitySpan]

