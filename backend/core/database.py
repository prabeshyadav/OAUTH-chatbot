from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import create_engine as sa_engine
import os

DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("DATABASE_PRIVATE_URL", "postgresql://postgres:postgres@db:5432/chatbot_db")

# Fix SQLAlchemy compatibility with Railway PostgreSQL URIs (postgres:// -> postgresql://)
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, echo=False)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session