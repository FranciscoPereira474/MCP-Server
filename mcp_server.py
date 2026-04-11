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
def add_item(name: str, price: float, description: str = "", quantity: int = 0, supplier_id: int | None = None, supplier_name: str | None = None) -> str:
    """Create a new item. If you know the supplier name (e.g. 'Worten'), pass it as supplier_name and the ID is looked up automatically. Only use supplier_id if you already know the numeric ID."""
    with Session(engine) as session:
        if supplier_name and not supplier_id:
            all_suppliers = get_suppliers(session, offset=0, limit=1000)
            match = next((s for s in all_suppliers if s.name.lower() == supplier_name.lower()), None)
            if match:
                supplier_id = match.id
            else:
                names = [s.name for s in all_suppliers]
                return f"ERROR: Supplier '{supplier_name}' not found. Available: {names}"
        item = create_item(
            session, ItemCreate(name=name, price=price, description=description, quantity=quantity, supplier_id=supplier_id)
        )
        return f"Item '{item.name}' created successfully."


@mcp.tool()
def list_all_items() -> str:
    """List all items in the inventory."""
    with Session(engine) as session:
        items = get_items(session, offset=0, limit=1000)
        if not items:
            return "No items found."
        lines = []
        for i in items:
            desc = f" — {i.description}" if i.description else ""
            supplier = get_supplier(session, i.supplier_id) if i.supplier_id else None
            supplier_info = f" | Supplier: {supplier.name}" if supplier else ""
            lines.append(f"- {i.name}{desc} | €{i.price} (qty: {i.quantity}){supplier_info}")
        return "\n".join(lines)


@mcp.tool()
def read_item(item_id: int | None = None, item_name: str | None = None) -> str:
    """Get details of an item by ID or by name."""
    with Session(engine) as session:
        if item_name and not item_id:
            all_items = get_items(session, offset=0, limit=1000)
            match = next((i for i in all_items if i.name.lower() == item_name.lower()), None)
            if match is None:
                return f"Item '{item_name}' not found."
            item_id = match.id
        if item_id is None:
            return "ERROR: Provide item_id or item_name."
        item = get_item(session, item_id)
        if item is None:
            return f"Item not found."
        supplier = get_supplier(session, item.supplier_id) if item.supplier_id else None
        supplier_info = f" | Supplier: {supplier.name}" if supplier else ""
        return f"{item.name}: {item.description} | €{item.price} (qty: {item.quantity}){supplier_info}"


@mcp.tool()
def modify_item(
    item_id: str = "",
    item_name: str = "",
    name: str = "",
    price: str = "",
    description: str = "",
    quantity: str = "",
    supplier_name: str = "",
) -> str:
    """Update an existing item by item_id or item_name. Pass item_name if you only know the name. Only pass the fields you want to change — leave others empty."""
    kwargs = {}
    if name.strip(): kwargs["name"] = name.strip()
    if price.strip():
        try: kwargs["price"] = float(price)
        except ValueError: return f"ERROR: Invalid price '{price}'."
    if description.strip(): kwargs["description"] = description.strip()
    if quantity.strip():
        try: kwargs["quantity"] = int(quantity)
        except ValueError: return f"ERROR: Invalid quantity '{quantity}'."
    parsed_item_id = None
    if item_id.strip():
        try: parsed_item_id = int(item_id)
        except ValueError: pass
    with Session(engine) as session:
        if supplier_name.strip():
            all_suppliers = get_suppliers(session, offset=0, limit=1000)
            match = next((s for s in all_suppliers if s.name.lower() == supplier_name.strip().lower()), None)
            if match:
                kwargs["supplier_id"] = match.id
            else:
                return f"ERROR: Supplier '{supplier_name}' not found."
        if item_name.strip() and not parsed_item_id:
            all_items = get_items(session, offset=0, limit=1000)
            match = next((i for i in all_items if i.name.lower() == item_name.strip().lower()), None)
            if match is None:
                return f"ERROR: Item '{item_name}' not found."
            parsed_item_id = match.id
        if parsed_item_id is None:
            return "ERROR: Provide item_id or item_name."
        updated = update_item(session, parsed_item_id, ItemUpdate.model_validate(kwargs))
        if updated is None:
            return "Item not found."
        return f"Item '{updated.name}' updated successfully."


@mcp.tool()
def remove_item(item_id: int | None = None, item_name: str | None = None) -> str:
    """Delete an item by ID or by name. Pass item_name if you only know the name."""
    with Session(engine) as session:
        if item_name and not item_id:
            all_items = get_items(session, offset=0, limit=1000)
            match = next((i for i in all_items if i.name.lower() == item_name.lower()), None)
            if match is None:
                return f"ERROR: Item '{item_name}' not found."
            item_id = match.id
        if item_id is None:
            return "ERROR: Provide item_id or item_name."
        if delete_item(session, item_id):
            return f"Item deleted successfully."
        return f"Item not found."


# ── Special tools ────────────────────────────────────────────────────


@mcp.tool()
def transfer_stock(quantity: int, from_item_name: str | None = None, to_item_name: str | None = None, from_item_id: int | None = None, to_item_id: int | None = None) -> str:
    """Transfer stock quantity from one item to another. Use from_item_name and to_item_name (e.g. 'Mesa2', 'Mesa'). Raises an exception if stock is insufficient."""
    if quantity <= 0:
        raise ValueError("Quantity must be a positive integer.")
    with Session(engine) as session:
        all_items = get_items(session, offset=0, limit=1000)
        if from_item_name and not from_item_id:
            match = next((i for i in all_items if i.name.lower() == from_item_name.lower()), None)
            if match is None:
                raise ValueError(f"Source item '{from_item_name}' not found.")
            from_item_id = match.id
        if to_item_name and not to_item_id:
            match = next((i for i in all_items if i.name.lower() == to_item_name.lower()), None)
            if match is None:
                raise ValueError(f"Destination item '{to_item_name}' not found.")
            to_item_id = match.id
        if from_item_id is None or to_item_id is None:
            raise ValueError("Provide from_item_name and to_item_name.")
        from_item = get_item(session, from_item_id)
        to_item = get_item(session, to_item_id)
        if from_item.quantity < quantity:
            raise ValueError(
                f"Insufficient stock: '{from_item.name}' only has {from_item.quantity} units, "
                f"cannot transfer {quantity}."
            )
        update_item(session, from_item_id, ItemUpdate.model_validate({"quantity": from_item.quantity - quantity}))
        update_item(session, to_item_id, ItemUpdate.model_validate({"quantity": to_item.quantity + quantity}))
        return f"Successfully transferred {quantity} units from '{from_item.name}' to '{to_item.name}'."


# ── Supplier tools ───────────────────────────────────────────────────


@mcp.tool()
def add_supplier(name: str, contact: str = "", email: str = "") -> str:
    """Create a new supplier."""
    with Session(engine) as session:
        supplier = create_supplier(
            session, SupplierCreate(name=name, contact=contact, email=email)
        )
        return f"Supplier '{supplier.name}' created successfully."


@mcp.tool()
def list_all_suppliers() -> str:
    """List all suppliers."""
    with Session(engine) as session:
        suppliers = get_suppliers(session, offset=0, limit=1000)
        if not suppliers:
            return "No suppliers found."
        lines = [f"- {s.name} | Contact: {s.contact} | Email: {s.email}" for s in suppliers]
        return "\n".join(lines)


@mcp.tool()
def read_supplier_tool(supplier_id: int) -> str:
    """Get details of a supplier by ID."""
    with Session(engine) as session:
        supplier = get_supplier(session, supplier_id)
        if supplier is None:
            return f"Supplier {supplier_id} not found."
        return f"{supplier.name} | Contact: {supplier.contact} | Email: {supplier.email}"


@mcp.tool()
def modify_supplier(
    supplier_id: int | None = None,
    supplier_name: str | None = None,
    name: str | None = None,
    contact: str | None = None,
    email: str | None = None,
) -> str:
    """Update an existing supplier by supplier_id or supplier_name."""
    kwargs = {}
    if name is not None: kwargs["name"] = name
    if contact is not None: kwargs["contact"] = contact
    if email is not None: kwargs["email"] = email
    with Session(engine) as session:
        if supplier_name and not supplier_id:
            all_suppliers = get_suppliers(session, offset=0, limit=1000)
            match = next((s for s in all_suppliers if s.name.lower() == supplier_name.lower()), None)
            if match is None:
                return f"ERROR: Supplier '{supplier_name}' not found."
            supplier_id = match.id
        if supplier_id is None:
            return "ERROR: Provide supplier_id or supplier_name."
        updated = update_supplier(session, supplier_id, SupplierUpdate.model_validate(kwargs))
        if updated is None:
            return "Supplier not found."
        return f"Supplier '{updated.name}' updated successfully."


@mcp.tool()
def remove_supplier(supplier_id: int | None = None, supplier_name: str | None = None) -> str:
    """Delete a supplier by ID or name. IMPORTANT: If the supplier still has items linked, return the error message to the user and STOP — do NOT delete the items first or take any other action."""
    with Session(engine) as session:
        if supplier_name and not supplier_id:
            all_suppliers = get_suppliers(session, offset=0, limit=1000)
            match = next((s for s in all_suppliers if s.name.lower() == supplier_name.lower()), None)
            if match is None:
                return f"ERROR: Supplier '{supplier_name}' not found."
            supplier_id = match.id
        if supplier_id is None:
            return "ERROR: Provide supplier_id or supplier_name."
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
        return f"Supplier '{supplier.name}' deleted successfully."


@mcp.tool()
def add_item_text(name: str, price: str, description: str = "", quantity: str = "0", supplier_id: str = "") -> str:
    """Create a new item using text-only inputs. All parameters are strings. Price should be a numeric string like '999.99'. Quantity should be an integer string like '10'. supplier_id can be a numeric ID string OR a supplier name like 'Fnac' — the system will look it up automatically."""
    parsed_price = float(price)
    parsed_qty = int(quantity) if quantity else 0
    parsed_supplier = None
    with Session(engine) as session:
        if supplier_id:
            try:
                parsed_supplier = int(supplier_id)
            except ValueError:
                all_suppliers = get_suppliers(session, offset=0, limit=1000)
                match = next((s for s in all_suppliers if s.name.lower() == supplier_id.lower()), None)
                if match:
                    parsed_supplier = match.id
                else:
                    names = [s.name for s in all_suppliers]
                    return f"ERROR: Supplier '{supplier_id}' not found. Available: {names}"
        item = create_item(
            session, ItemCreate(name=name, price=parsed_price, description=description, quantity=parsed_qty, supplier_id=parsed_supplier)
        )
        supplier = get_supplier(session, item.supplier_id) if item.supplier_id else None
        supplier_info = supplier.name if supplier else "none"
        return (
            f"Item '{item.name}' created successfully | "
            f"Price: €{item.price:.2f} | Qty: {item.quantity} | "
            f"Supplier: {supplier_info}"
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
