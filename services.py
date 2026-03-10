"""Shared business logic used by both the FastAPI routes and the MCP tools."""


def say_hello(name: str = "World") -> str:
    """Return a hello-world greeting."""
    return f"Hello, {name}!"
