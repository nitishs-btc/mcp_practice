from __future__ import annotations

from starlette.testclient import TestClient

from philter_mcp_server.agent.app import create_app
from philter_mcp_server.agent.models import RedactionResult


class FakePipeline:
    async def redact(self, text: str) -> RedactionResult:
        assert text == (
            "George Washington lives in 90210 and his SSN was 123-45-6789"
        )
        return RedactionResult(
            redacted_text=(
                "{{{REDACTED-first-name}}} {{{REDACTED-first-name}}} lives in "
                "{{{REDACTED-zip-code}}} and his SSN was {{{REDACTED-ssn}}}"
            )
        )


def test_redact_endpoint_returns_redacted_text() -> None:
    app = create_app(pipeline=FakePipeline())

    with TestClient(app) as client:
        response = client.post(
            "/redact",
            json={
                "text": "George Washington lives in 90210 and his SSN was 123-45-6789"
            },
        )

    assert response.status_code == 200
    assert response.json() == {
        "redacted_text": (
            "{{{REDACTED-first-name}}} {{{REDACTED-first-name}}} lives in "
            "{{{REDACTED-zip-code}}} and his SSN was {{{REDACTED-ssn}}}"
        )
    }
