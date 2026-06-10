"""Simple MCP client for local verification."""

from __future__ import annotations

import asyncio
import json
import os

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def main() -> None:
    url = os.getenv("PHILTER_MCP_URL", "http://localhost:8000/mcp")
    sample_text = "Patient Name: Example Person\nEmail: demo.user@example.com"

    async with streamable_http_client(url) as (read_stream, write_stream, _):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            result = await session.call_tool("redact_text", {"text": sample_text})
            print(json.dumps(result.structuredContent, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
