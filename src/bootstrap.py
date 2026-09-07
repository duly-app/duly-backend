from src.adapters.orm import start_mappers
from src.db import create_session_factory
from src.environment import EnvVar
from src.service.uow import SQLAlchemyUOW, UOWFactory


def bootstrap(config: dict) -> UOWFactory:
    start_mappers()
    uow_factory = get_uow_factory(config)

    return uow_factory


def get_uow_factory(config: dict) -> UOWFactory:
    db_url = config[EnvVar.DATABASE_URL]
    session_factory = create_session_factory(db_url)

    def uow_factory() -> SQLAlchemyUOW:
        return SQLAlchemyUOW(session_maker=session_factory)

    return uow_factory
