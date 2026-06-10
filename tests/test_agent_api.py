from __future__ import annotations

from starlette.testclient import TestClient

from philter_mcp_server.agent.app import create_app
from philter_mcp_server.agent.models import RedactionResult
from philter_mcp_server.models import EntitySpan


class FakePipeline:
    async def redact(self, text: str) -> RedactionResult:
        del text
        return RedactionResult(
            entities=[
                EntitySpan(
                    entity_type="name",
                    start=14,
                    end=28,
                    confidence=0.95,
                ),
                EntitySpan(
                    entity_type="email",
                    start=36,
                    end=57,
                    confidence=0.99,
                ),
            ]
        )


def test_redact_endpoint_returns_entity_spans() -> None:
    app = create_app(pipeline=FakePipeline())

    with TestClient(app) as client:
        response = client.post(
            "/redact",
            json={"text": "Patient Name: Example Person\nEmail: demo.user@example.com"},
        )

    assert response.status_code == 200
    assert response.json() == {
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

