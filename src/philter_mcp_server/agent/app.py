"""Public HTTP API that exposes a single redaction endpoint."""

from __future__ import annotations

from contextlib import asynccontextmanager

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route
from pydantic import ValidationError

from philter_mcp_server.agent.config import AgentSettings, settings
from philter_mcp_server.agent.models import RedactionRequest
from philter_mcp_server.agent.pipeline import RedactionPipeline
from philter_mcp_server.logging_utils import configure_logging


logger = configure_logging(settings.log_level)


def create_app(
    agent_settings: AgentSettings = settings,
    pipeline: RedactionPipeline | None = None,
) -> Starlette:
    """Create the Starlette app used by the public integration surface."""

    @asynccontextmanager
    async def lifespan(app: Starlette):
        app.state.pipeline = pipeline or await RedactionPipeline.build(agent_settings)
        logger.info(
            "agent_service_ready host=%s port=%d mcp_url=%s tool=%s",
            agent_settings.host,
            agent_settings.port,
            agent_settings.mcp_url,
            agent_settings.mcp_tool_name,
        )
        yield

    async def redact_endpoint(request: Request) -> JSONResponse:
        pipeline: RedactionPipeline = request.app.state.pipeline

        try:
            payload = RedactionRequest.model_validate(await request.json())
        except ValidationError as exc:
            return JSONResponse({"detail": exc.errors()}, status_code=422)

        result = await pipeline.redact(payload.text)
        return JSONResponse(result.model_dump())

    return Starlette(
        routes=[Route("/redact", endpoint=redact_endpoint, methods=["POST"])],
        lifespan=lifespan,
    )


app = create_app()
