"""Provider factory."""

from __future__ import annotations

from philter_mcp_server.config import Settings
from philter_mcp_server.providers.base import DetectionProvider
from philter_mcp_server.providers.philter_api import PhilterAPIRedactionProvider
from philter_mcp_server.providers.rule_based import RuleBasedDetectionProvider


def build_provider(settings: Settings) -> DetectionProvider:
    """Instantiate the configured provider."""

    if settings.provider == "philter-api":
        return PhilterAPIRedactionProvider(
            api_url=settings.philter_api_url,
            timeout_seconds=settings.philter_api_timeout_seconds,
            verify_ssl=settings.philter_api_verify_ssl,
        )

    return RuleBasedDetectionProvider()
