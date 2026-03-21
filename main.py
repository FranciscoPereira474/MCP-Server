from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlmodel import Session

from database import create_db_and_tables, get_session
from models import Item, ItemCreate, ItemUpdate
from services import (
    create_item,
    delete_item,
    get_item,
    get_items,
    say_hello,
    update_item,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(title="MCP-IS-PROJECT", version="0.1.0", lifespan=lifespan)


@app.get("/")
async def root(name: str = "World") -> dict:
    return {"message": say_hello(name)}


@app.post("/items", response_model=Item, status_code=201)
def create_item_endpoint(
    item: ItemCreate, session: Session = Depends(get_session)
):
    return create_item(session, item)


@app.get("/items", response_model=list[Item])
def list_items(
    offset: int = 0, limit: int = 100, session: Session = Depends(get_session)
):
    return get_items(session, offset=offset, limit=limit)


@app.get("/items/{item_id}", response_model=Item)
def read_item(item_id: int, session: Session = Depends(get_session)):
    item = get_item(session, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.patch("/items/{item_id}", response_model=Item)
def update_item_endpoint(
    item_id: int, item: ItemUpdate, session: Session = Depends(get_session)
):
    updated = update_item(session, item_id, item)
    if updated is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return updated


@app.delete("/items/{item_id}", status_code=204)
def delete_item_endpoint(item_id: int, session: Session = Depends(get_session)):
    if not delete_item(session, item_id):
        raise HTTPException(status_code=404, detail="Item not found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
