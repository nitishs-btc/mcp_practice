"""Executable entrypoint for the public redaction API."""

from __future__ import annotations

import uvicorn

from philter_mcp_server.agent.app import app
from philter_mcp_server.agent.config import settings


def main() -> None:
    """Run the agentic redaction API over HTTP."""

    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
