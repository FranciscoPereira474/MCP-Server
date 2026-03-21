from sqlmodel import Field, SQLModel


class ItemBase(SQLModel):
    name: str = Field(index=True)
    description: str | None = None
    price: float = Field(ge=0)
    quantity: int = Field(default=0, ge=0)


class Item(ItemBase, table=True):
    id: int | None = Field(default=None, primary_key=True)


class ItemCreate(ItemBase):
    pass


class ItemUpdate(SQLModel):
    name: str | None = None
    description: str | None = None
    price: float | None = Field(default=None, ge=0)
    quantity: int | None = Field(default=None, ge=0)
