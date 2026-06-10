"""LangGraph pipeline that orchestrates the MCP tool call."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, TYPE_CHECKING, TypedDict

from philter_mcp_server.agent.config import AgentSettings
from philter_mcp_server.agent.models import RedactionResult

if TYPE_CHECKING:
    from langchain_core.tools import BaseTool


class RedactionState(TypedDict, total=False):
    """State shared across the LangGraph workflow."""

    text: str
    raw_result: Any
    redacted_text: str


@dataclass(slots=True)
class RedactionPipeline:
    """Async LangGraph workflow that calls one MCP tool."""

    mcp_client: Any
    redact_tool: Any
    graph: Any

    @classmethod
    async def build(cls, settings: AgentSettings) -> "RedactionPipeline":
        """Connect to the upstream MCP server and build the workflow."""

        try:
            from langchain_mcp_adapters.client import MultiServerMCPClient
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "langchain-mcp-adapters is not installed in the active Python environment. "
                "Run `uv sync` and start the app with `.venv/bin/python -m philter_mcp_server` "
                "or `uv run python -m philter_mcp_server`."
            ) from exc

        client = MultiServerMCPClient(
            {
                settings.mcp_server_name: {
                    "transport": "http",
                    "url": settings.mcp_url,
                }
            }
        )
        tools = await client.get_tools()
        redact_tool = cls._find_redact_tool(tools, settings.mcp_tool_name)
        pipeline = cls(mcp_client=client, redact_tool=redact_tool, graph=None)
        pipeline.graph = pipeline._build_graph()
        return pipeline

    async def redact(self, text: str) -> RedactionResult:
        """Run the workflow and return redacted text."""

        result = await self.graph.ainvoke({"text": text})
        return RedactionResult(redacted_text=result.get("redacted_text", ""))

    def _build_graph(self) -> Any:
        try:
            from langgraph.graph import END, START, StateGraph
        except ModuleNotFoundError as exc:
            raise RuntimeError(
                "langgraph is not installed in the active Python environment. "
                "Run `uv sync` and start the app with `.venv/bin/python -m philter_mcp_server` "
                "or `uv run python -m philter_mcp_server`."
            ) from exc

        workflow = StateGraph(RedactionState)
        workflow.add_node("prepare", self._prepare)
        workflow.add_node("redact", self._redact)
        workflow.add_node("finish", self._finish)

        workflow.add_edge(START, "prepare")
        workflow.add_conditional_edges(
            "prepare",
            self._route_from_prepare,
            {
                "redact": "redact",
                "finish": "finish",
            },
        )
        workflow.add_edge("redact", "finish")
        workflow.add_edge("finish", END)
        return workflow.compile()

    @staticmethod
    def _find_redact_tool(tools: list[Any], tool_name: str) -> Any:
        for tool in tools:
            if tool.name == tool_name:
                return tool

        available = ", ".join(sorted(tool.name for tool in tools))
        raise RuntimeError(
            f"Could not find MCP tool {tool_name!r}. Available tools: {available or 'none'}."
        )

    async def _prepare(self, state: RedactionState) -> dict[str, Any]:
        text = state["text"].strip()
        return {"text": text, "redacted_text": ""}

    @staticmethod
    def _route_from_prepare(state: RedactionState) -> str:
        return "redact" if state.get("text") else "finish"

    async def _redact(self, state: RedactionState) -> dict[str, Any]:
        tool_result = await self.redact_tool.ainvoke({"text": state["text"]})
        redacted_text = self._extract_redacted_text(tool_result)
        return {"raw_result": tool_result, "redacted_text": redacted_text}

    async def _finish(self, state: RedactionState) -> dict[str, Any]:
        return {"redacted_text": state.get("redacted_text", "")}

    def _extract_redacted_text(self, raw_result: Any) -> str:
        if raw_result is None:
            return ""

        if isinstance(raw_result, list):
            for item in raw_result:
                redacted_text = self._extract_redacted_text(item)
                if redacted_text:
                    return redacted_text
            return ""

        if isinstance(raw_result, str):
            parsed = self._maybe_parse_json(raw_result)
            if isinstance(parsed, dict):
                return self._extract_redacted_text(parsed)
            if isinstance(parsed, list):
                return self._extract_redacted_text(parsed)
            return raw_result

        if isinstance(raw_result, dict):
            for key in ("redacted_text", "redactedText"):
                value = raw_result.get(key)
                if isinstance(value, str):
                    return value

            for key in ("structured_content", "structuredContent", "content", "artifact"):
                nested = raw_result.get(key)
                if nested is not None:
                    redacted_text = self._extract_redacted_text(nested)
                    if redacted_text:
                        return redacted_text

            return ""

        content = getattr(raw_result, "content", None)
        if content is not None:
            redacted_text = self._extract_redacted_text(content)
            if redacted_text:
                return redacted_text

        structured_content = getattr(raw_result, "structured_content", None)
        if structured_content is not None:
            redacted_text = self._extract_redacted_text(structured_content)
            if redacted_text:
                return redacted_text

        artifact = getattr(raw_result, "artifact", None)
        if artifact is not None:
            redacted_text = self._extract_redacted_text(artifact)
            if redacted_text:
                return redacted_text

        parsed = self._maybe_parse_json(raw_result)
        if isinstance(parsed, dict):
            return self._extract_redacted_text(parsed)
        if isinstance(parsed, list):
            return self._extract_redacted_text(parsed)
        if isinstance(parsed, str):
            return parsed

        return str(raw_result)

    @staticmethod
    def _maybe_parse_json(value: Any) -> Any:
        if not isinstance(value, str):
            return value

        try:
            return json.loads(value)
        except ValueError:
            return value
