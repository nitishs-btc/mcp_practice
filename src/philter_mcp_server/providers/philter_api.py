"""Optional provider that adapts an external Philter API."""

from __future__ import annotations

from typing import Any

import httpx

from philter_mcp_server.models import EntitySpan
from philter_mcp_server.providers.base import DetectionProvider, ProviderError


class PhilterAPIDetectionProvider(DetectionProvider):
    """Provider that calls a Philter-compatible HTTP API and extracts spans."""

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

    async def detect_entities(self, text: str) -> list[EntitySpan]:
        timeout = httpx.Timeout(self.timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout, verify=self.verify_ssl) as client:
            response = await client.post(
                self.api_url,
                content=text,
                headers={"Content-Type": "text/plain"},
            )
            response.raise_for_status()

        try:
            payload = response.json()
        except ValueError as exc:
            raise ProviderError(
                "Configured Philter API did not return JSON span data."
            ) from exc

        entities = self._extract_entities(payload)
        if not entities:
            raise ProviderError(
                "Configured Philter API response did not include detectable span metadata."
            )

        return entities

    async def health(self) -> dict[str, object]:
        return {
            "provider": self.name,
            "status": "configured",
            "api_url": self.api_url,
        }

    def _extract_entities(self, payload: Any) -> list[EntitySpan]:
        raw_entities = self._find_candidate_entity_list(payload)
        spans: list[EntitySpan] = []

        for item in raw_entities:
            if not isinstance(item, dict):
                continue

            start = self._coerce_int(
                item.get("start")
                or item.get("begin")
                or item.get("beginOffset")
                or item.get("startOffset")
            )
            end = self._coerce_int(
                item.get("end")
                or item.get("stop")
                or item.get("endOffset")
                or item.get("stopOffset")
            )
            entity_type = self._normalize_entity_type(
                item.get("entity_type")
                or item.get("entityType")
                or item.get("type")
                or item.get("label")
                or item.get("classification")
            )
            confidence = self._coerce_float(
                item.get("confidence")
                or item.get("score")
                or item.get("probability")
                or 0.90
            )

            if entity_type and start is not None and end is not None and end >= start:
                spans.append(
                    EntitySpan(
                        entity_type=entity_type,
                        start=start,
                        end=end,
                        confidence=max(0.0, min(confidence, 1.0)),
                    )
                )

        return sorted(spans, key=lambda entity: (entity.start, entity.end, entity.entity_type))

    def _find_candidate_entity_list(self, payload: Any) -> list[Any]:
        if isinstance(payload, list):
            return payload
        if not isinstance(payload, dict):
            return []

        for key in ("entities", "spans", "findings", "matches", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return value
            if isinstance(value, dict):
                nested = self._find_candidate_entity_list(value)
                if nested:
                    return nested

        for value in payload.values():
            nested = self._find_candidate_entity_list(value)
            if nested:
                return nested

        return []

    @staticmethod
    def _coerce_int(value: Any) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _coerce_float(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.90

    @staticmethod
    def _normalize_entity_type(value: Any) -> str | None:
        if not value:
            return None

        normalized = str(value).strip().lower().replace("_", "-").replace(" ", "-")
        aliases = {
            "person": "name",
            "person-name": "name",
            "patient-name": "name",
            "full-name": "name",
            "mail": "email",
            "e-mail": "email",
            "email-address": "email",
            "phone-number": "phone",
            "telephone": "phone",
            "social-security-number": "ssn",
        }
        return aliases.get(normalized, normalized)
