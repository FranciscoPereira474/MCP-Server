from mcp.server.fastmcp import FastMCP

from services import say_hello

mcp = FastMCP("mcp-is-project")


@mcp.tool()
def hello(name: str = "World") -> str:
    """Say hello to someone."""
    return say_hello(name)


if __name__ == "__main__":
    mcp.run()
