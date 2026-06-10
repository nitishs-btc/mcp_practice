"""Rule-based fallback provider for PHI/PII span detection."""

from __future__ import annotations

import re

from philter_mcp_server.models import EntitySpan
from philter_mcp_server.providers.base import DetectionProvider


class RuleBasedDetectionProvider(DetectionProvider):
    """Detect a small set of PHI/PII entities with regex rules."""

    name = "rule-based"

    def __init__(self) -> None:
        self._patterns: tuple[tuple[str, re.Pattern[str], float, str | None], ...] = (
            (
                "name",
                re.compile(
                    r"(?i)\b(?:patient\s+name|name|full\s+name)\s*:\s*(?P<value>[A-Z][a-z]+(?:[ '-][A-Z][a-z]+){0,3})"
                ),
                0.95,
                "value",
            ),
            (
                "email",
                re.compile(
                    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
                ),
                0.99,
                None,
            ),
            (
                "phone",
                re.compile(
                    r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?){2}\d{4}\b"
                ),
                0.97,
                None,
            ),
            (
                "ssn",
                re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
                0.99,
                None,
            ),
        )

    async def detect_entities(self, text: str) -> list[EntitySpan]:
        matches: list[EntitySpan] = []

        for entity_type, pattern, confidence, group_name in self._patterns:
            for match in pattern.finditer(text):
                if group_name is None:
                    start, end = match.span()
                else:
                    start, end = match.span(group_name)
                matches.append(
                    EntitySpan(
                        entity_type=entity_type,
                        start=start,
                        end=end,
                        confidence=confidence,
                    )
                )

        deduplicated: dict[tuple[str, int, int], EntitySpan] = {}
        for entity in matches:
            key = (entity.entity_type, entity.start, entity.end)
            deduplicated[key] = entity

        return sorted(
            deduplicated.values(),
            key=lambda entity: (entity.start, entity.end, entity.entity_type),
        )
