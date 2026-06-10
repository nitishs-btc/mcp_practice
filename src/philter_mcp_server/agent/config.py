"""Configuration for the public agent API."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AgentSettings(BaseSettings):
    """Runtime settings for the LangChain/LangGraph agent service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = Field(default="127.0.0.1", alias="PHILTER_AGENT_HOST")
    port: int = Field(default=8000, alias="PHILTER_AGENT_PORT")
    log_level: str = Field(default="INFO", alias="PHILTER_AGENT_LOG_LEVEL")
    mcp_url: str = Field(
        default="http://localhost:8001/mcp",
        alias="PHILTER_MCP_URL",
    )
    mcp_server_name: str = Field(default="philter", alias="PHILTER_MCP_SERVER_NAME")
    mcp_tool_name: str = Field(default="redact_text", alias="PHILTER_MCP_TOOL_NAME")


settings = AgentSettings()

