"""Request and response models for the public agent API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RedactionRequest(BaseModel):
    """Input payload accepted by the public API."""

    text: str = Field(description="Plain text to send to the redaction pipeline.")


class RedactionResult(BaseModel):
    """Response payload returned by the public API."""

    redacted_text: str = Field(description="Redacted text returned by the MCP tool.")
