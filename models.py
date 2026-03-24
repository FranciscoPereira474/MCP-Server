from sqlmodel import Field, Relationship, SQLModel


# ── Supplier ─────────────────────────────────────────────────────────


class SupplierBase(SQLModel):
    name: str = Field(index=True)
    contact: str | None = None
    email: str | None = None


class Supplier(SupplierBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    items: list["Item"] = Relationship(back_populates="supplier")


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(SQLModel):
    name: str | None = None
    contact: str | None = None
    email: str | None = None


# ── Item ─────────────────────────────────────────────────────────────


class ItemBase(SQLModel):
    name: str = Field(index=True)
    description: str | None = None
    price: float = Field(ge=0)
    quantity: int = Field(default=0, ge=0)
    supplier_id: int | None = Field(default=None, foreign_key="supplier.id")


class Item(ItemBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    supplier: Supplier | None = Relationship(back_populates="items")


class ItemCreate(ItemBase):
    pass


class ItemUpdate(SQLModel):
    name: str | None = None
    description: str | None = None
    price: float | None = Field(default=None, ge=0)
    quantity: int | None = Field(default=None, ge=0)
    supplier_id: int | None = None
