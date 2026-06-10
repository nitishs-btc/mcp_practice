"""LangGraph pipeline that orchestrates the MCP tool call."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, TYPE_CHECKING, TypedDict

from philter_mcp_server.agent.config import AgentSettings
from philter_mcp_server.agent.models import RedactionResult
from philter_mcp_server.models import EntitySpan

if TYPE_CHECKING:
    from langchain_core.tools import BaseTool


class RedactionState(TypedDict, total=False):
    """State shared across the LangGraph workflow."""

    text: str
    should_detect: bool
    raw_result: Any
    entities: list[EntitySpan]


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
        """Run the workflow and return normalized entity spans."""

        result = await self.graph.ainvoke({"text": text})
        entities = result.get("entities", [])
        return RedactionResult(entities=entities)

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
        workflow.add_node("detect", self._detect)
        workflow.add_node("normalize", self._normalize)
        workflow.add_node("finish", self._finish)

        workflow.add_edge(START, "prepare")
        workflow.add_conditional_edges(
            "prepare",
            self._route_from_prepare,
            {
                "detect": "detect",
                "finish": "finish",
            },
        )
        workflow.add_edge("detect", "normalize")
        workflow.add_edge("normalize", "finish")
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
        return {
            "text": text,
            "should_detect": bool(text),
            "entities": [],
        }

    @staticmethod
    def _route_from_prepare(state: RedactionState) -> str:
        return "detect" if state.get("should_detect") else "finish"

    async def _detect(self, state: RedactionState) -> dict[str, Any]:
        tool_result = await self.redact_tool.ainvoke({"text": state["text"]})
        return {"raw_result": tool_result}

    async def _normalize(self, state: RedactionState) -> dict[str, Any]:
        structured = self._extract_structured_content(state.get("raw_result"))
        entities = self._parse_entities(structured)
        return {"entities": entities}

    async def _finish(self, state: RedactionState) -> dict[str, Any]:
        return {"entities": state.get("entities", [])}

    def _extract_structured_content(self, raw_result: Any) -> dict[str, Any]:
        if raw_result is None:
            return {}

        if isinstance(raw_result, dict):
            nested = raw_result.get("structured_content") or raw_result.get(
                "structuredContent"
            )
            if isinstance(nested, dict):
                return nested
            if "entities" in raw_result:
                return raw_result

        artifact = getattr(raw_result, "artifact", None)
        if isinstance(artifact, dict):
            nested = artifact.get("structured_content") or artifact.get(
                "structuredContent"
            )
            if isinstance(nested, dict):
                return nested
            return artifact

        structured_content = getattr(raw_result, "structured_content", None)
        if isinstance(structured_content, dict):
            return structured_content

        content = getattr(raw_result, "content", None)
        if isinstance(content, dict):
            return content
        if isinstance(content, str):
            parsed = self._maybe_parse_json(content)
            if isinstance(parsed, dict):
                return parsed

        parsed = self._maybe_parse_json(raw_result)
        if isinstance(parsed, dict):
            return parsed

        return {}

    @staticmethod
    def _maybe_parse_json(value: Any) -> Any:
        if not isinstance(value, str):
            return value

        try:
            return json.loads(value)
        except ValueError:
            return value

    def _parse_entities(self, payload: dict[str, Any]) -> list[EntitySpan]:
        raw_entities = payload.get("entities")
        if not isinstance(raw_entities, list):
            raw_entities = payload.get("spans")
        if not isinstance(raw_entities, list):
            raw_entities = []

        entities: list[EntitySpan] = []
        for item in raw_entities:
            entity = self._coerce_entity(item)
            if entity is not None:
                entities.append(entity)

        deduplicated: dict[tuple[str, int, int], EntitySpan] = {}
        for entity in entities:
            key = (entity.entity_type, entity.start, entity.end)
            deduplicated[key] = entity

        return sorted(
            deduplicated.values(),
            key=lambda entity: (entity.start, entity.end, entity.entity_type),
        )

    def _coerce_entity(self, item: Any) -> EntitySpan | None:
        if isinstance(item, EntitySpan):
            return item
        if not isinstance(item, dict):
            return None

        entity_type = self._normalize_entity_type(
            item.get("entity_type")
            or item.get("entityType")
            or item.get("type")
            or item.get("label")
            or item.get("classification")
        )
        start = self._coerce_int(
            item.get("start")
            or item.get("begin")
            or item.get("beginOffset")
            or item.get("startOffset")
        )
        end = self._coerce_int(
            item.get("end")
            or item.get("stop")
            or item.get("endOffset")
            or item.get("stopOffset")
        )
        confidence = self._coerce_float(
            item.get("confidence")
            or item.get("score")
            or item.get("probability")
            or 0.90
        )

        if entity_type and start is not None and end is not None and end >= start:
            return EntitySpan(
                entity_type=entity_type,
                start=start,
                end=end,
                confidence=max(0.0, min(confidence, 1.0)),
            )

        return None

    @staticmethod
    def _normalize_entity_type(value: Any) -> str | None:
        if not value:
            return None

        normalized = str(value).strip().lower().replace("_", "-").replace(" ", "-")
        aliases = {
            "person": "name",
            "person-name": "name",
            "patient-name": "name",
            "full-name": "name",
            "mail": "email",
            "e-mail": "email",
            "email-address": "email",
            "phone-number": "phone",
            "telephone": "phone",
            "social-security-number": "ssn",
        }
        return aliases.get(normalized, normalized)

    @staticmethod
    def _coerce_int(value: Any) -> int | None:
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _coerce_float(value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.90
