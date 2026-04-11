"""LangChain agent that connects to the MCP server and uses Ollama as LLM."""

import logging
from pathlib import Path

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_ollama import ChatOllama
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent

MCP_CONFIG = {
    "mcp-is-project": {
        "command": "uv",
        "args": ["run", "python", str(BASE_DIR / "mcp_server.py")],
        "transport": "stdio",
    }
}

_agent = None
_client = None  # kept alive so the MCP subprocess stays running
_memory = MemorySaver()
_llm = ChatOllama(model="llama3.2", temperature=0)


async def initialize_agent() -> None:
    """Start the MCP subprocess once and build the LangChain agent."""
    global _agent, _client

    logger.info("Initializing MCP client...")
    _client = MultiServerMCPClient(MCP_CONFIG)
    tools = await _client.get_tools()
    logger.info(f"Loaded {len(tools)} MCP tools: {[t.name for t in tools]}")

    system_prompt = (
        "You are an inventory management assistant. "
        "You help users manage items and suppliers in a database. "
        "IMPORTANT RULES:\n"
        "- When deleting a supplier, call remove_supplier ONCE and report the result to the user. "
        "If it returns an error because items are linked, tell the user and STOP — do NOT delete the items.\n"
        "- When the user mentions a supplier by name, use the supplier_name parameter in add_item instead of looking up the ID manually.\n"
        "- Always confirm actions before reporting success."
    )
    _agent = create_react_agent(_llm, tools, checkpointer=_memory, prompt=system_prompt)
    logger.info("LangChain agent ready.")


async def shutdown_agent() -> None:
    """No-op: process cleanup handled by OS."""
    pass


def _clear_thread(thread_id: str) -> None:
    """Remove all checkpoints for a given thread to reset corrupted memory."""
    keys = [k for k in _memory.storage.keys() if thread_id in str(k)]
    for k in keys:
        del _memory.storage[k]


async def get_agent_response(message: str, thread_id: str = "default") -> str:
    """Send a message to the agent and return its text response.

    The thread_id keeps conversation memory isolated per browser session.
    If the memory is corrupted (e.g. after a failed tool call), the thread is
    reset automatically and the message is retried.
    """
    config = {"configurable": {"thread_id": thread_id}}
    try:
        result = await _agent.ainvoke(
            {"messages": [{"role": "user", "content": message}]},
            config,
        )
        return result["messages"][-1].content
    except Exception as e:
        if "INVALID_CHAT_HISTORY" in str(e) or "ToolMessage" in str(e):
            logger.warning("Corrupted chat history detected — resetting thread and retrying.")
            _clear_thread(thread_id)
            result = await _agent.ainvoke(
                {"messages": [{"role": "user", "content": message}]},
                config,
            )
            return result["messages"][-1].content
        raise
