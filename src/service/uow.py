from __future__ import annotations

from abc import ABC, abstractmethod
from contextlib import AbstractContextManager
from typing import Callable, Self, TypeAlias

from sqlalchemy.orm import sessionmaker

from src.adapters.repository import (
    AbstractUserRepository,
    NotesRepository,
    SQLAlchemyNoteEventStore,
    SQLAlchemyNoteProjection,
    SQLAlchemyUserRepository,
)

UOWFactory: TypeAlias = Callable[[], "AbstractUOW"]


class AbstractUOW(AbstractContextManager, ABC):
    users: AbstractUserRepository
    notes: NotesRepository

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

    @abstractmethod
    def check_health(self) -> None:
        pass


class SQLAlchemyUOW(AbstractUOW):
    _session_maker: sessionmaker

    def __init__(self, session_maker: sessionmaker):
        self._session_maker = session_maker

    def __enter__(self) -> "SQLAlchemyUOW":
        self._session = self._session_maker()
        self.users = SQLAlchemyUserRepository(self._session)
        self.notes = NotesRepository(
            SQLAlchemyNoteEventStore(self._session),
            SQLAlchemyNoteProjection(self._session),
        )

        return super().__enter__()

    def __exit__(self, *args) -> None:
        super().__exit__(*args)
        self._session.close()

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()

    def check_health(self) -> None:
        self._session.execute("SELECT 1")
