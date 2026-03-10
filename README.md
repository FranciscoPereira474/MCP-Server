# mcp-is-project

Hello World FastAPI + MCP server project managed with **uv**.

## Requirements

- [uv](https://docs.astral.sh/uv/) — Python package & project manager

## Setup

```bash
uv sync --dev
```

## Run

### FastAPI server

```bash
uv run uvicorn main:app --reload
```

Endpoints:
- `GET /` → `{"message": "Hello World"}`
- `GET /health` → `{"status": "ok"}`
- `GET /docs` → Swagger UI

### MCP server (stdio transport)

```bash
uv run python mcp_server.py
```

## Development tools

| Tool | Purpose |
|------|---------|
| `uv run ruff check .` | Linting |
| `uv run ruff format .` | Formatting |
| `uv run pytest` | Tests |
