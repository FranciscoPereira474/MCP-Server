from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlmodel import Session

from agent import get_agent_response, initialize_agent, shutdown_agent
from database import create_db_and_tables, get_session
from models import Item, ItemCreate, ItemUpdate, Supplier, SupplierCreate, SupplierUpdate
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


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"


class ChatResponse(BaseModel):
    response: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    await initialize_agent()
    yield
    await shutdown_agent()


app = FastAPI(title="MCP-IS-PROJECT", version="0.1.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/ui")
async def serve_ui():
    return FileResponse("static/chat.html")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    import traceback
    try:
        response = await get_agent_response(request.message, request.thread_id)
        return ChatResponse(response=response)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


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


# ── Supplier endpoints ───────────────────────────────────────────────


@app.post("/suppliers", response_model=Supplier, status_code=201)
def create_supplier_endpoint(
    supplier: SupplierCreate, session: Session = Depends(get_session)
):
    return create_supplier(session, supplier)


@app.get("/suppliers", response_model=list[Supplier])
def list_suppliers(
    offset: int = 0, limit: int = 100, session: Session = Depends(get_session)
):
    return get_suppliers(session, offset=offset, limit=limit)


@app.get("/suppliers/{supplier_id}", response_model=Supplier)
def read_supplier(supplier_id: int, session: Session = Depends(get_session)):
    supplier = get_supplier(session, supplier_id)
    if supplier is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return supplier


@app.patch("/suppliers/{supplier_id}", response_model=Supplier)
def update_supplier_endpoint(
    supplier_id: int, supplier: SupplierUpdate, session: Session = Depends(get_session)
):
    updated = update_supplier(session, supplier_id, supplier)
    if updated is None:
        raise HTTPException(status_code=404, detail="Supplier not found")
    return updated


@app.delete("/suppliers/{supplier_id}", status_code=204)
def delete_supplier_endpoint(supplier_id: int, session: Session = Depends(get_session)):
    if not delete_supplier(session, supplier_id):
        raise HTTPException(status_code=404, detail="Supplier not found")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
