from __future__ import annotations

import importlib
from collections.abc import AsyncGenerator

import pytest
from mcp.client.session import ClientSession
from mcp.shared.memory import create_connected_server_and_client_session


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def mcp_module(monkeypatch: pytest.MonkeyPatch):
    from philter_mcp_server import app as app_module

    module = importlib.reload(app_module)

    class FakeProvider:
        name = "fake-provider"

        async def redact_text(self, text: str) -> str:
            assert text == (
                "George Washington lives in 90210 and his SSN was 123-45-6789"
            )
            return (
                "{{{REDACTED-first-name}}} {{{REDACTED-first-name}}} lives in "
                "{{{REDACTED-zip-code}}} and his SSN was {{{REDACTED-ssn}}}"
            )

        async def health(self) -> dict[str, object]:
            return {
                "provider": self.name,
                "status": "configured",
                "mode": "redact_text",
            }

    monkeypatch.setattr(module, "provider", FakeProvider())
    return module


@pytest.fixture
async def client_session(mcp_module) -> AsyncGenerator[ClientSession]:
    async with create_connected_server_and_client_session(
        mcp_module.mcp, raise_exceptions=True
    ) as session:
        yield session


@pytest.mark.anyio
async def test_redact_text_tool_returns_redacted_text(
    client_session: ClientSession,
) -> None:
    text = "George Washington lives in 90210 and his SSN was 123-45-6789"

    result = await client_session.call_tool("redact_text", {"text": text})

    assert result.structuredContent == {
        "redacted_text": (
            "{{{REDACTED-first-name}}} {{{REDACTED-first-name}}} lives in "
            "{{{REDACTED-zip-code}}} and his SSN was {{{REDACTED-ssn}}}"
        )
    }


@pytest.mark.anyio
async def test_health_tool_reports_configured_provider(
    client_session: ClientSession,
) -> None:
    result = await client_session.call_tool("health")

    assert result.structuredContent["status"] == "ok"
    assert result.structuredContent["provider"] == "fake-provider"
    assert result.structuredContent["details"]["mode"] == "redact_text"
