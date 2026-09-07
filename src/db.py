from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def create_session_factory(database_url: str) -> sessionmaker:
    engine = create_engine(database_url)
    SessionFactory = sessionmaker(bind=engine)

    return SessionFactory
