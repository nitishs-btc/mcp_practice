"""Optional provider that adapts an external Philter API."""

from __future__ import annotations

import httpx

from philter_mcp_server.detection_models import EntitySpan
from philter_mcp_server.providers.base import DetectionProvider, ProviderError


class PhilterAPIRedactionProvider(DetectionProvider):
    """Provider that calls a Philter-compatible HTTP API and returns redacted text."""

    name = "philter-api"

    def __init__(
        self,
        api_url: str,
        timeout_seconds: float = 10.0,
        verify_ssl: bool = False,
    ) -> None:
        self.api_url = api_url
        self.timeout_seconds = timeout_seconds
        self.verify_ssl = verify_ssl

    async def redact_text(self, text: str) -> str:
        timeout = httpx.Timeout(self.timeout_seconds)
        try:
            async with httpx.AsyncClient(
                timeout=timeout,
                verify=self.verify_ssl,
            ) as client:
                response = await client.post(
                    self.api_url,
                    content=text,
                    headers={
                        "Content-Type": "text/plain",
                        "Authorization": "Bearer default",
                    },
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            raise ProviderError("Configured Philter API request failed.") from exc

        return response.text

    async def detect_entities(self, text: str) -> list[EntitySpan]:
        raise ProviderError(
            "Configured Philter API returns redacted text and does not expose spans."
        )

    async def health(self) -> dict[str, object]:
        return {
            "provider": self.name,
            "status": "configured",
            "mode": "redact_text",
            "api_url": self.api_url,
        }


PhilterAPIDetectionProvider = PhilterAPIRedactionProvider
