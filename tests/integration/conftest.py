from typing import NamedTuple, Protocol

import pytest

from src.adapters.repository import AbstractUserRepository, NotesRepository
from src.service.uow import AbstractUOW
from tests.integration.fakes.fake_notes_repo import create_fake_notes_repo
from tests.integration.fakes.fake_uow import FakeUOW
from tests.integration.fakes.fake_user_repo import FakeUserRepository
from tests.integration.fakes.helpers import get_note_events, get_users, parse_db


class FakeDB(NamedTuple):
    users: AbstractUserRepository
    notes: NotesRepository


class UserRepoFactory(Protocol):
    def __call__(self, db_name: str) -> AbstractUserRepository: ...


class NotesRepoFactory(Protocol):
    def __call__(self, db_name: str) -> NotesRepository: ...


class DBFactory(Protocol):
    def __call__(self, db_name: str) -> FakeDB: ...


class UOWFactory(Protocol):
    def __call__(self, db_name: str) -> "AbstractUOW": ...


@pytest.fixture
def create_user_repo() -> UserRepoFactory:
    def _user_repo_factory(db_name: str) -> AbstractUserRepository:
        users = get_users(db_name)

        return FakeUserRepository(users=users)

    return _user_repo_factory


@pytest.fixture
def create_notes_repo() -> NotesRepoFactory:
    def _notes_repo_factory(db_name: str) -> NotesRepository:
        return create_fake_notes_repo(get_note_events(db_name))

    return _notes_repo_factory


@pytest.fixture
def create_db(
    create_user_repo: UserRepoFactory, create_notes_repo: NotesRepoFactory
) -> DBFactory:
    def _db_factory(db_name: str) -> FakeDB:
        return FakeDB(users=create_user_repo(db_name), notes=create_notes_repo(db_name))

    return _db_factory


@pytest.fixture
def create_uow() -> UOWFactory:
    def _uow_factory(db_name: str) -> AbstractUOW:
        users, note_events = parse_db(db_name)

        return FakeUOW(users=users, note_events=note_events)

    return _uow_factory
