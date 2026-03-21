import os
from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("A variável de ambiente DATABASE_URL não está definida. Por favor, configura-a no ficheiro .env")

engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    from models import Item  # noqa: F401 – ensure model is registered

    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
