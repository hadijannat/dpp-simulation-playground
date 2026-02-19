from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from ..config import DATABASE_URL
from services.shared.tracing import instrument_sqlalchemy_engine

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
instrument_sqlalchemy_engine(engine, service_name="simulation-engine")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
