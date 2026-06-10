"""ASGI application and MCP tool registration."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager

from mcp.server.fastmcp import Context, FastMCP
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from philter_mcp_server.config import settings
from philter_mcp_server.logging_utils import configure_logging
from philter_mcp_server.models import HealthResponse, RedactionResponse
from philter_mcp_server.providers.base import ProviderError
from philter_mcp_server.providers.factory import build_provider


logger = configure_logging(settings.log_level)
provider = build_provider(settings)

mcp = FastMCP(
    name="Philter Detector MCP",
    instructions=(
        "Redact PHI/PII by calling the upstream Philter API. "
        "The redact_text tool returns redacted text, not spans."
    ),
    stateless_http=True,
    json_response=True,
    streamable_http_path="/mcp",
)


@mcp.tool(name="redact_text")
async def redact_text(text: str, ctx: Context) -> RedactionResponse:
    """Redact PHI/PII in text and return the masked output."""

    started_at = time.perf_counter()
    request_id = str(ctx.request_id)
    text_length = len(text)

    try:
        redacted_text = await provider.redact_text(text)
    except ProviderError as exc:
        duration_ms = (time.perf_counter() - started_at) * 1000
        logger.error(
            "redact_text_failed request_id=%s provider=%s text_length=%d duration_ms=%.2f error_type=%s",
            request_id,
            provider.name,
            text_length,
            duration_ms,
            exc.__class__.__name__,
        )
        raise RuntimeError("Text redaction failed.") from exc

    duration_ms = (time.perf_counter() - started_at) * 1000
    logger.info(
        "redact_text_completed request_id=%s provider=%s text_length=%d duration_ms=%.2f",
        request_id,
        provider.name,
        text_length,
        duration_ms,
    )
    return RedactionResponse(redacted_text=redacted_text)


@mcp.tool(name="health")
async def health(ctx: Context) -> HealthResponse:
    """Report safe server and provider health information."""

    del ctx
    details = await provider.health()
    return HealthResponse(status="ok", provider=provider.name, details=details)


async def health_endpoint(_request) -> JSONResponse:
    """Simple HTTP health endpoint."""

    details = await provider.health()
    return JSONResponse(
        {
            "status": "ok",
            "provider": provider.name,
            "mode": details.get("mode", "unknown"),
        }
    )


@asynccontextmanager
async def lifespan(_app: Starlette):
    async with mcp.session_manager.run():
        yield


app = Starlette(
    routes=[
        Route("/healthz", endpoint=health_endpoint, methods=["GET"]),
        Mount("/", app=mcp.streamable_http_app()),
    ],
    lifespan=lifespan,
)
