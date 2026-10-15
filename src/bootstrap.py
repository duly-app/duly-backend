from dataclasses import dataclass

from src.adapters.orm import start_mappers
from src.adapters.security.argon_password_service import ArgonPasswordService
from src.adapters.security.password_service import PasswordService
from src.adapters.security.service_token_service import ServiceTokenService
from src.adapters.security.token_service import TokenService
from src.db import create_session_factory
from src.environment import EnvVar
from src.service.uow import SQLAlchemyUOW, UOWFactory


@dataclass(frozen=True)
class Dependencies:
    uow_factory: UOWFactory
    password_service: PasswordService
    token_service: TokenService
    service_token_service: ServiceTokenService


def bootstrap(config: dict) -> Dependencies:
    start_mappers()

    return Dependencies(
        uow_factory=get_uow_factory(config),
        password_service=ArgonPasswordService(),
        token_service=TokenService(secret_key=config[EnvVar.SIGNING_KEY]),
        service_token_service=ServiceTokenService(
            secret_key=config[EnvVar.SERVICE_KEY]
        ),
    )


def get_uow_factory(config: dict) -> UOWFactory:
    db_url = config[EnvVar.DATABASE_URL]
    session_factory = create_session_factory(db_url)

    def uow_factory() -> SQLAlchemyUOW:
        return SQLAlchemyUOW(session_maker=session_factory)

    return uow_factory
