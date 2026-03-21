from mcp.server.fastmcp import FastMCP
from sqlmodel import Session

from database import create_db_and_tables, engine
from models import ItemCreate, ItemUpdate
from services import (
    create_item,
    delete_item,
    get_item,
    get_items,
    say_hello,
    update_item,
)

mcp = FastMCP("mcp-is-project")

create_db_and_tables()


@mcp.tool()
def hello(name: str = "World") -> str:
    """Say hello to someone."""
    return say_hello(name)


@mcp.tool()
def add_item(name: str, price: float, description: str = "", quantity: int = 0) -> str:
    """Create a new item."""
    with Session(engine) as session:
        item = create_item(
            session, ItemCreate(name=name, price=price, description=description, quantity=quantity)
        )
        return f"Created item {item.id}: {item.name}"


@mcp.tool()
def list_all_items(offset: int = 0, limit: int = 100) -> str:
    """List all items."""
    with Session(engine) as session:
        items = get_items(session, offset=offset, limit=limit)
        if not items:
            return "No items found."
        lines = [f"- [{i.id}] {i.name}: {i.description} | €{i.price} (qty: {i.quantity})" for i in items]
        return "\n".join(lines)


@mcp.tool()
def read_item(item_id: int) -> str:
    """Get details of an item by ID."""
    with Session(engine) as session:
        item = get_item(session, item_id)
        if item is None:
            return f"Item {item_id} not found."
        return f"[{item.id}] {item.name}: {item.description} | €{item.price} (qty: {item.quantity})"


@mcp.tool()
def modify_item(
    item_id: int,
    name: str | None = None,
    price: float | None = None,
    description: str | None = None,
    quantity: int | None = None,
) -> str:
    """Update an existing item."""
    with Session(engine) as session:
        updated = update_item(
            session, item_id, ItemUpdate(name=name, price=price, description=description, quantity=quantity)
        )
        if updated is None:
            return f"Item {item_id} not found."
        return f"Updated item {updated.id}: {updated.name}"


@mcp.tool()
def remove_item(item_id: int) -> str:
    """Delete an item by ID."""
    with Session(engine) as session:
        if delete_item(session, item_id):
            return f"Item {item_id} deleted."
        return f"Item {item_id} not found."


if __name__ == "__main__":
    mcp.run()
