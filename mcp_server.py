from pathlib import Path

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


BASE_DIR = Path(__file__).parent


@mcp.resource("resource://db-model")
def get_db_model() -> str:
    """Returns the database model documentation describing all tables and columns."""
    return (BASE_DIR / "db_model.txt").read_text(encoding="utf-8")


@mcp.resource("resource://internal-report")
def get_internal_report() -> str:
    """Returns an internal report with system overview, endpoints, and architecture."""
    return (BASE_DIR / "internal_report.txt").read_text(encoding="utf-8")


@mcp.prompt()
def inventory_report(sort_by: str = "name") -> str:
    """Generate an inventory report sorted by a given criterion (name, price, or quantity)."""
    return (
        f"Use the 'list_all_items' tool to retrieve every item in the database. "
        f"Then organize the results into a well-formatted inventory report sorted by {sort_by}. "
        f"The report should include:\n"
        f"1. A header with the report title and the current date.\n"
        f"2. A table or list of all items showing: ID, Name, Description, Price, and Quantity.\n"
        f"3. A summary section at the end with:\n"
        f"   - Total number of items\n"
        f"   - Total inventory value (sum of price * quantity for each item)\n"
        f"   - Item with the highest price\n"
        f"   - Item with the lowest stock (quantity)\n"
        f"Sort all items by '{sort_by}' in ascending order."
    )


if __name__ == "__main__":
    mcp.run()
