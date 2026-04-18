# MCP Inventory Manager

An AI-powered inventory management system built with **FastAPI**, **Model Context Protocol (MCP)**, and **LangChain**. A conversational AI agent (powered by Ollama/Llama 3.2) manages items and suppliers in a PostgreSQL database through natural language commands.

> Academic project for the **Enterprise Application Integration (IS)** course — Master's in Computer Engineering, University of Coimbra, 2025/2026.

## Features

- **Natural Language Interface** — manage inventory through a chat UI powered by an LLM agent
- **Full CRUD** — create, read, update, and delete items and suppliers
- **Stock Transfers** — transfer quantities between items with validation
- **Supplier Management** — link items to suppliers, lookup by name
- **MCP Server** — tools exposed via the Model Context Protocol for AI agent integration
- **REST API** — standard FastAPI endpoints alongside the AI chat interface

## Architecture

```
Browser (Chat UI)
      │
      │ HTTP
      ▼
  FastAPI Server
      │
      ├── /chat endpoint ──> LangChain Agent (Ollama/Llama 3.2)
      │                            │
      │                      MCP Tools (stdio)
      │                            │
      │                      MCP Server (FastMCP)
      │                            │
      ├── REST endpoints ──────────┤
      │                            │
      ▼                            ▼
  SQLModel / PostgreSQL
```

The LangChain agent uses a ReAct pattern with MCP tools to interpret user requests, call the appropriate inventory operations, and return natural language responses.

## Tech Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.12 |
| Web Framework | FastAPI + Uvicorn |
| AI Agent | LangChain + LangGraph |
| LLM | Ollama (Llama 3.2) |
| MCP | FastMCP (Model Context Protocol) |
| ORM | SQLModel |
| Database | PostgreSQL |
| Package Manager | uv |

## Getting Started

### Prerequisites

- Python 3.12+
- PostgreSQL
- [Ollama](https://ollama.com/) with `llama3.2` model pulled
- [uv](https://docs.astral.sh/uv/) package manager

### Setup

```bash
# Install dependencies
uv sync

# Configure database connection
# Create a .env file with:
DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:5432/mcp_is_project"

# Run the server
uv run python main.py
```

The app will be available at:
- Chat UI: `http://localhost:8000/ui`
- REST API: `http://localhost:8000/docs`

## Project Structure

```
MCP-IS-PROJECT/
├── main.py            # FastAPI app with REST endpoints and chat
├── mcp_server.py      # MCP server with all inventory tools
├── agent.py           # LangChain ReAct agent with Ollama
├── models.py          # SQLModel data models (Item, Supplier)
├── services.py        # Business logic layer
├── database.py        # Database connection and setup
├── static/            # Chat UI frontend
├── db_model.txt       # Database schema documentation
└── pyproject.toml     # Dependencies and project config
```

## Team

- Francisco Pereira
- Tiago Mendes

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
