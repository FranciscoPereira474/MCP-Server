from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = "postgresql://postgres:postgres@127.0.0.1:5432/mcp_is_project"

engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    from models import Item  # noqa: F401 – ensure model is registered

    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
