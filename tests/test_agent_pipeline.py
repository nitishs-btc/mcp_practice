from __future__ import annotations

import pytest

from philter_mcp_server.agent.pipeline import RedactionPipeline


class FakeRedactTool:
    name = "redact_text"

    async def ainvoke(self, input_data: dict[str, str]) -> dict[str, object]:
        assert input_data == {
            "text": "George Washington lives in 90210 and his SSN was 123-45-6789"
        }
        return {
            "structuredContent": {
                "redacted_text": (
                    "{{{REDACTED-first-name}}} {{{REDACTED-first-name}}} lives in "
                    "{{{REDACTED-zip-code}}} and his SSN was {{{REDACTED-ssn}}}"
                )
            }
        }


@pytest.mark.anyio
async def test_pipeline_returns_redacted_text() -> None:
    pipeline = RedactionPipeline(
        mcp_client=None,
        redact_tool=FakeRedactTool(),
        graph=None,
    )
    pipeline.graph = pipeline._build_graph()

    result = await pipeline.redact(
        "George Washington lives in 90210 and his SSN was 123-45-6789"
    )

    assert result.redacted_text == (
        "{{{REDACTED-first-name}}} {{{REDACTED-first-name}}} lives in "
        "{{{REDACTED-zip-code}}} and his SSN was {{{REDACTED-ssn}}}"
    )
