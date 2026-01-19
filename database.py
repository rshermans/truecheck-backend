from sqlmodel import SQLModel, create_engine, Session
from config import settings
import os

# Ensure data directory exists if using SQLite and path is local
if settings.DATABASE_URL.startswith("sqlite"):
    os.makedirs("data", exist_ok=True)

connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, connect_args=connect_args)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
