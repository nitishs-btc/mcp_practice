"""Safe logging configuration for the MCP server."""

from __future__ import annotations

import logging


def configure_logging(log_level: str) -> logging.Logger:
    """Configure application logging without emitting request text."""

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    return logging.getLogger("philter_mcp_server")
