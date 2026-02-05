from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def get_engine(database_url: str):
    return create_engine(database_url, future=True)


def get_session_factory(database_url: str):
    engine = get_engine(database_url)
    return sessionmaker(bind=engine, autoflush=False, autocommit=False)
