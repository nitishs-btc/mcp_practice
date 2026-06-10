# Philter Agent API

Public redaction API built with LangChain, LangGraph, and `langchain-mcp-adapters`.

The service exposes one HTTP endpoint for other projects to call:

- `POST /redact`

That endpoint sends text to the upstream Philter MCP server through `langchain-mcp-adapters`, then normalizes the returned spans before responding.

## Flow

1. Receive a JSON payload with `text`.
2. Load the upstream `redact_text` MCP tool through `MultiServerMCPClient`.
3. Run a small LangGraph workflow to prepare, invoke, normalize, and finish the request.
4. Return entity spans only.

## Project Structure

```text
.
├── .env.example
├── pyproject.toml
├── README.md
├── src/
│   └── philter_mcp_server/
│       ├── __main__.py
│       ├── agent/
│       │   ├── __init__.py
│       │   ├── app.py
│       │   ├── config.py
│       │   ├── models.py
│       │   └── pipeline.py
│       ├── app.py
│       ├── config.py
│       ├── logging_utils.py
│       ├── models.py
│       └── providers/
└── tests/
```

The old MCP server modules remain in the repo, but the default entrypoint now launches the public agent API.

## Configuration

Copy `.env.example` to `.env` and adjust as needed:

```bash
cp .env.example .env
```

Available settings:

- `PHILTER_AGENT_HOST=127.0.0.1`
- `PHILTER_AGENT_PORT=8000`
- `PHILTER_AGENT_LOG_LEVEL=INFO`
- `PHILTER_MCP_URL=http://localhost:8001/mcp`
- `PHILTER_MCP_SERVER_NAME=philter`
- `PHILTER_MCP_TOOL_NAME=redact_text`
- `PHILTER_MCP_HOST=127.0.0.1`
- `PHILTER_MCP_PORT=8001`
- `PHILTER_MCP_LOG_LEVEL=INFO`
- `PHILTER_MCP_PROVIDER=rule-based`

## Setup

Using `uv`:

```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

Using `pip`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run

Start the upstream MCP server first:

```bash
uv run philter-mcp-server
```

Then start the public agent API in a second terminal:

```bash
uv run philter-agent-api
```

The public API listens on `http://localhost:8000`.
The MCP tool server listens on `http://localhost:8001/mcp`.

## API Contract

Request:

```json
{
  "text": "Patient Name: Example Person\nEmail: demo.user@example.com"
}
```

Response:

```json
{
  "entities": [
    {
      "entity_type": "name",
      "start": 14,
      "end": 28,
      "confidence": 0.95
    },
    {
      "entity_type": "email",
      "start": 36,
      "end": 57,
      "confidence": 0.99
    }
  ]
}
```

## Example Call

```bash
curl -X POST http://localhost:8000/redact \
  -H "Content-Type: application/json" \
  -d '{"text":"Patient Name: Example Person\nEmail: demo.user@example.com"}'
```

## Notes

- The agent does not log raw text.
- The agent uses the upstream MCP tool through `langchain-mcp-adapters`.
- The LangGraph workflow is intentionally small and deterministic because the task is structured redaction, not free-form reasoning.

## Tests

```bash
source .venv/bin/activate
pytest
```
