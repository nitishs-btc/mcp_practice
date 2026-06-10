from __future__ import annotations

import httpx
import pytest

from philter_mcp_server.providers.philter_api import PhilterAPIRedactionProvider
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
async def test_rule_based_provider_redacts_text() -> None:
    provider = RuleBasedDetectionProvider()
    text = "Patient Name: Example Person\nEmail: demo.user@example.com"

    redacted_text = await provider.redact_text(text)

    assert redacted_text == (
        "Patient Name: {{{REDACTED-name}}}\nEmail: {{{REDACTED-email}}}"
    )


@pytest.mark.anyio
async def test_philter_api_provider_returns_plain_text_redaction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url == httpx.URL("https://192.168.0.32:8080/api/filter")
        assert request.headers["content-type"] == "text/plain"
        assert request.headers["authorization"] == "Bearer default"
        assert (
            request.content.decode()
            == "George Washington lives in 90210 and his SSN was 123-45-6789"
        )
        return httpx.Response(
            200,
            text=(
                "{{{REDACTED-first-name}}} {{{REDACTED-first-name}}} lives in "
                "{{{REDACTED-zip-code}}} and his SSN was {{{REDACTED-ssn}}}"
            ),
        )

    transport = httpx.MockTransport(handler)

    original_async_client = httpx.AsyncClient

    def mock_async_client(*args, **kwargs):
        kwargs["transport"] = transport
        return original_async_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "AsyncClient", mock_async_client)

    provider = PhilterAPIRedactionProvider("https://192.168.0.32:8080/api/filter")
    redacted_text = await provider.redact_text(
        "George Washington lives in 90210 and his SSN was 123-45-6789"
    )

    assert (
        redacted_text
        == "{{{REDACTED-first-name}}} {{{REDACTED-first-name}}} lives in {{{REDACTED-zip-code}}} and his SSN was {{{REDACTED-ssn}}}"
    )
