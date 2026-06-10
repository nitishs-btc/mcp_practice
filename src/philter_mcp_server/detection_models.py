"""Models used by entity-detection providers."""

from __future__ import annotations

from pydantic import BaseModel, Field


class EntitySpan(BaseModel):
    """A detected PHI/PII entity span."""

    entity_type: str = Field(
        description="Normalized entity type, for example name or email."
    )
    start: int = Field(ge=0, description="Start character offset, inclusive.")
    end: int = Field(ge=0, description="End character offset, exclusive.")
    confidence: float = Field(ge=0.0, le=1.0, description="Detection confidence.")
