from __future__ import annotations

import httpx
import pytest

from philter_mcp_server.providers.philter_api import PhilterAPIDetectionProvider
from philter_mcp_server.providers.rule_based import RuleBasedDetectionProvider


@pytest.mark.anyio
async def test_rule_based_provider_detects_name_and_email() -> None:
    provider = RuleBasedDetectionProvider()
    text = "Patient Name: Example Person\nEmail: demo.user@example.com"

    entities = await provider.detect_entities(text)

    assert [entity.model_dump() for entity in entities] == [
        {
            "entity_type": "name",
            "start": 14,
            "end": 28,
            "confidence": 0.95,
        },
        {
            "entity_type": "email",
            "start": 36,
            "end": 57,
            "confidence": 0.99,
        },
    ]


@pytest.mark.anyio
async def test_philter_api_provider_maps_span_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == httpx.URL("http://localhost:8080/api/filter")
        assert request.headers["content-type"] == "text/plain"
        return httpx.Response(
            200,
            json={
                "spans": [
                    {
                        "entityType": "PERSON_NAME",
                        "start": 14,
                        "end": 28,
                        "confidence": 0.94,
                    },
                    {
                        "type": "EMAIL_ADDRESS",
                        "startOffset": 36,
                        "endOffset": 57,
                        "score": 0.99,
                    },
                ]
            },
        )

    transport = httpx.MockTransport(handler)

    original_async_client = httpx.AsyncClient

    def mock_async_client(*args, **kwargs):
        kwargs["transport"] = transport
        return original_async_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", mock_async_client)

    provider = PhilterAPIDetectionProvider("http://localhost:8080/api/filter")
    entities = await provider.detect_entities(
        "Patient Name: Example Person\nEmail: demo.user@example.com"
    )

    assert [entity.model_dump() for entity in entities] == [
        {
            "entity_type": "name",
            "start": 14,
            "end": 28,
            "confidence": 0.94,
        },
        {
            "entity_type": "email",
            "start": 36,
            "end": 57,
            "confidence": 0.99,
        },
    ]
