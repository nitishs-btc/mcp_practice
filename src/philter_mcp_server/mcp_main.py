"""Executable entrypoint for the upstream Philter MCP server."""

from __future__ import annotations

import uvicorn

from philter_mcp_server.app import app
from philter_mcp_server.config import settings


def main() -> None:
    """Run the MCP tool server over streamable HTTP."""

    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )


if __name__ == "__main__":
    main()
