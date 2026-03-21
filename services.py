"""Shared business logic used by both the FastAPI routes and the MCP tools."""

from sqlmodel import Session, select

from models import Item, ItemCreate, ItemUpdate


def say_hello(name: str = "World") -> str:
    """Return a hello-world greeting."""
    return f"Hello, {name}!"


def create_item(session: Session, item_data: ItemCreate) -> Item:
    item = Item.model_validate(item_data)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def get_item(session: Session, item_id: int) -> Item | None:
    return session.get(Item, item_id)


def get_items(session: Session, offset: int = 0, limit: int = 100) -> list[Item]:
    return list(session.exec(select(Item).offset(offset).limit(limit)).all())


def update_item(session: Session, item_id: int, item_data: ItemUpdate) -> Item | None:
    item = session.get(Item, item_id)
    if item is None:
        return None
    update_dict = item_data.model_dump(exclude_unset=True)
    item.sqlmodel_update(update_dict)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


def delete_item(session: Session, item_id: int) -> bool:
    item = session.get(Item, item_id)
    if item is None:
        return False
    session.delete(item)
    session.commit()
    return True
