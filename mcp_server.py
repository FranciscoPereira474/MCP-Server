from pathlib import Path

from mcp.server.fastmcp import FastMCP
from sqlmodel import Session, select

from database import create_db_and_tables, engine
from models import Item, ItemCreate, ItemUpdate, SupplierCreate, SupplierUpdate
from services import (
    create_item,
    create_supplier,
    delete_item,
    delete_supplier,
    get_item,
    get_items,
    get_supplier,
    get_suppliers,
    say_hello,
    update_item,
    update_supplier,
)

mcp = FastMCP("mcp-is-project")

create_db_and_tables()


@mcp.tool()
def hello(name: str = "World") -> str:
    """Say hello to someone."""
    return say_hello(name)


@mcp.tool()
def add_item(name: str, price: float, description: str = "", quantity: int = 0, supplier_id: int | None = None) -> str:
    """Create a new item. The supplier_id is the numeric ID of an existing supplier. If the user provides a supplier name instead of an ID, use the list_all_suppliers tool first to find the correct ID."""
    with Session(engine) as session:
        item = create_item(
            session, ItemCreate(name=name, price=price, description=description, quantity=quantity, supplier_id=supplier_id)
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
    supplier_id: int | None = None,
) -> str:
    """Update an existing item. The supplier_id is the numeric ID of an existing supplier. If the user provides a supplier name instead of an ID, use the list_all_suppliers tool first to find the correct ID."""
    kwargs = {}
    if name is not None: kwargs["name"] = name
    if price is not None: kwargs["price"] = price
    if description is not None: kwargs["description"] = description
    if quantity is not None: kwargs["quantity"] = quantity
    if supplier_id is not None: kwargs["supplier_id"] = supplier_id
    with Session(engine) as session:
        updated = update_item(
            session, item_id, ItemUpdate.model_validate(kwargs)
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


# ── Special tools ────────────────────────────────────────────────────


@mcp.tool()
def transfer_stock(from_item_id: int, to_item_id: int, quantity: int) -> str:
    """Transfer stock quantity from one item to another. Both items must exist. The quantity must be positive and the source item must have enough stock available. Raises an exception if stock is insufficient."""
    if quantity <= 0:
        raise ValueError("Quantity must be a positive integer.")
    with Session(engine) as session:
        from_item = get_item(session, from_item_id)
        if from_item is None:
            raise ValueError(f"Source item {from_item_id} not found.")
        to_item = get_item(session, to_item_id)
        if to_item is None:
            raise ValueError(f"Destination item {to_item_id} not found.")
        if from_item.quantity < quantity:
            raise ValueError(
                f"Insufficient stock: '{from_item.name}' only has {from_item.quantity} units, "
                f"cannot transfer {quantity}."
            )
        update_item(session, from_item_id, ItemUpdate.model_validate({"quantity": from_item.quantity - quantity}))
        update_item(session, to_item_id, ItemUpdate.model_validate({"quantity": to_item.quantity + quantity}))
        return (
            f"Transferred {quantity} units from '{from_item.name}' to '{to_item.name}'. "
            f"New stock: {from_item.name}={from_item.quantity - quantity}, {to_item.name}={to_item.quantity + quantity}"
        )


# ── Supplier tools ───────────────────────────────────────────────────


@mcp.tool()
def add_supplier(name: str, contact: str = "", email: str = "") -> str:
    """Create a new supplier."""
    with Session(engine) as session:
        supplier = create_supplier(
            session, SupplierCreate(name=name, contact=contact, email=email)
        )
        return f"Created supplier {supplier.id}: {supplier.name}"


@mcp.tool()
def list_all_suppliers(offset: int = 0, limit: int = 100) -> str:
    """List all suppliers."""
    with Session(engine) as session:
        suppliers = get_suppliers(session, offset=offset, limit=limit)
        if not suppliers:
            return "No suppliers found."
        lines = [f"- [{s.id}] {s.name} | Contact: {s.contact} | Email: {s.email}" for s in suppliers]
        return "\n".join(lines)


@mcp.tool()
def read_supplier_tool(supplier_id: int) -> str:
    """Get details of a supplier by ID."""
    with Session(engine) as session:
        supplier = get_supplier(session, supplier_id)
        if supplier is None:
            return f"Supplier {supplier_id} not found."
        return f"[{supplier.id}] {supplier.name} | Contact: {supplier.contact} | Email: {supplier.email}"


@mcp.tool()
def modify_supplier(
    supplier_id: int,
    name: str | None = None,
    contact: str | None = None,
    email: str | None = None,
) -> str:
    """Update an existing supplier."""
    kwargs = {}
    if name is not None: kwargs["name"] = name
    if contact is not None: kwargs["contact"] = contact
    if email is not None: kwargs["email"] = email
    with Session(engine) as session:
        updated = update_supplier(
            session, supplier_id, SupplierUpdate.model_validate(kwargs)
        )
        if updated is None:
            return f"Supplier {supplier_id} not found."
        return f"Updated supplier {updated.id}: {updated.name}"


@mcp.tool()
def remove_supplier(supplier_id: int) -> str:
    """Delete a supplier by ID. Returns an error if the supplier still has items linked."""
    with Session(engine) as session:
        supplier = get_supplier(session, supplier_id)
        if supplier is None:
            return "ERROR: Supplier not found."
        items = list(session.exec(select(Item).where(Item.supplier_id == supplier_id)).all())
        if items:
            item_names = ", ".join(i.name for i in items)
            return (
                f"ERROR: Cannot delete supplier '{supplier.name}' because they still have "
                f"{len(items)} item(s) linked: {item_names}. "
                f"Remove or reassign these items first."
            )
        delete_supplier(session, supplier_id)
        return f"Supplier '{supplier.name}' (ID: {supplier_id}) deleted successfully."


@mcp.tool()
def add_item_text(name: str, price: str, description: str = "", quantity: str = "0", supplier_id: str = "") -> str:
    """Create a new item using text-only inputs. All parameters are strings. Price should be a numeric string like '999.99'. Quantity should be an integer string like '10'. Supplier_id should be a numeric string or empty. This is an alternative to add_item that accepts all values as text."""
    parsed_price = float(price)
    parsed_qty = int(quantity)
    parsed_supplier = int(supplier_id) if supplier_id else None
    with Session(engine) as session:
        item = create_item(
            session, ItemCreate(name=name, price=parsed_price, description=description, quantity=parsed_qty, supplier_id=parsed_supplier)
        )
        return (
            f"Created item {item.id}: {item.name} | "
            f"Price: €{item.price:.2f} | Qty: {item.quantity} | "
            f"Supplier ID: {item.supplier_id or 'none'}"
        )


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
