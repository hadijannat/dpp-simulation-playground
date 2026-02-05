from sqlalchemy import create_engine, Table, Column, String
from sqlalchemy.orm import sessionmaker
from ..config import DATABASE_URL

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

if DATABASE_URL.startswith("sqlite"):
    from ..models.base import Base

    if "simulation_sessions" not in Base.metadata.tables:
        Table("simulation_sessions", Base.metadata, Column("id", String, primary_key=True))

    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
