"""Provider abstraction for entity detection."""

from __future__ import annotations

from abc import ABC, abstractmethod

from philter_mcp_server.models import EntitySpan


class ProviderError(RuntimeError):
    """Raised when a provider cannot complete a detection request safely."""


class DetectionProvider(ABC):
    """Interface for PHI/PII detection providers."""

    name: str

    @abstractmethod
    async def detect_entities(self, text: str) -> list[EntitySpan]:
        """Detect entities in text and return spans only."""

    async def health(self) -> dict[str, object]:
        """Return provider health metadata."""

        return {"provider": self.name, "status": "ok"}
