from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from typing import Callable, Self, TypeAlias

from sqlalchemy.orm import sessionmaker

from src.adapters.repository import AbstractUserRepository, SQLAlchemyUserRepository

UOWFactory: TypeAlias = Callable[[], "AbstractUOW"]


class AbstractUOW(AbstractContextManager, ABC):
    users: AbstractUserRepository

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args) -> None:
        self.rollback()

    @abstractmethod
    def commit(self) -> None:
        pass

    @abstractmethod
    def rollback(self) -> None:
        pass


class SQLAlchemyUOW(AbstractUOW):
    _session_maker: sessionmaker

    def __init__(self, session_maker: sessionmaker):
        self._session_maker = session_maker

    def __enter__(self) -> "SQLAlchemyUOW":
        self._session = self._session_maker()
        self.users = SQLAlchemyUserRepository(self._session)

        return super().__enter__()

    def __exit__(self, *args) -> None:
        super().__exit__(*args)
        self._session.close()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()
