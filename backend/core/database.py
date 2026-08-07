from sqlmodel import SQLModel, create_engine, Session
from sqlalchemy import create_engine as sa_engine
import os
import time

DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("DATABASE_PRIVATE_URL", "postgresql://postgres:postgres@db:5432/chatbot_db")

# Fix SQLAlchemy compatibility with Railway PostgreSQL URIs (postgres:// -> postgresql://)
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300
)

def create_db_and_tables():
    max_retries = 5
    for attempt in range(max_retries):
        try:
            SQLModel.metadata.create_all(engine)
            print("Database connected and tables verified.")
            return
        except Exception as e:
            print(f"Database connection attempt {attempt + 1}/{max_retries} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                print("Warning: Could not connect to Database on startup. Server will continue.")

def get_session():
    with Session(engine) as session:
        yield session