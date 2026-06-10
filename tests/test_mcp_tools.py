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
def mcp_server(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("PHILTER_MCP_PROVIDER", "rule-based")
    from philter_mcp_server import app as app_module

    return importlib.reload(app_module).mcp


@pytest.fixture
async def client_session(mcp_server) -> AsyncGenerator[ClientSession]:
    async with create_connected_server_and_client_session(
        mcp_server, raise_exceptions=True
    ) as session:
        yield session


@pytest.mark.anyio
async def test_redact_text_tool_returns_expected_spans(
    client_session: ClientSession,
) -> None:
    text = "Patient Name: Example Person\nEmail: demo.user@example.com"

    result = await client_session.call_tool("redact_text", {"text": text})

    assert result.structuredContent == {
        "entities": [
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
    }


@pytest.mark.anyio
async def test_health_tool_reports_configured_provider(
    client_session: ClientSession,
) -> None:
    result = await client_session.call_tool("health")

    assert result.structuredContent["status"] == "ok"
    assert result.structuredContent["provider"] == "rule-based"
