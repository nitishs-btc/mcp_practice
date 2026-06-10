"""Provider abstraction for redaction and entity detection."""

from __future__ import annotations

from abc import ABC

from philter_mcp_server.detection_models import EntitySpan


class ProviderError(RuntimeError):
    """Raised when a provider cannot complete a request safely."""


class DetectionProvider(ABC):
    """Interface for PHI/PII redaction and detection providers."""

    name: str

    async def redact_text(self, text: str) -> str:
        """Redact text and return the masked output."""

        raise ProviderError(f"Provider {self.name!r} does not support redaction.")

    async def detect_entities(self, text: str) -> list[EntitySpan]:
        """Detect entities in text and return spans only."""

        raise ProviderError(
            f"Provider {self.name!r} does not support entity detection."
        )

    async def health(self) -> dict[str, object]:
        """Return provider health metadata."""

        return {"provider": self.name, "status": "ok"}
