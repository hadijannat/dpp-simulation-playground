from sqlalchemy import create_engine, Table, Column, String, Integer
from sqlalchemy.orm import sessionmaker
from ..config import DATABASE_URL

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, future=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

if DATABASE_URL.startswith("sqlite"):
    from ..models.base import Base

    if "users" not in Base.metadata.tables:
        Table("users", Base.metadata, Column("id", String, primary_key=True))
    if "user_stories" not in Base.metadata.tables:
        Table("user_stories", Base.metadata, Column("id", Integer, primary_key=True))

    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
