from typing import Protocol

import pytest

from src.adapters.user_repo import AbstractUserRepository
from src.service.uow import AbstractUOW
from tests.integration.fakes.fake_uow import FakeUOW
from tests.integration.fakes.fake_user_repo import FakeUserRepository
from tests.integration.fakes.helpers import get_users


class UserRepoFactory(Protocol):
    def __call__(self, repo_name: str) -> AbstractUserRepository: ...


class UOWFactory(Protocol):
    def __call__(self, repo_name: str) -> "AbstractUOW": ...


@pytest.fixture
def create_user_repo() -> UserRepoFactory:
    def _user_repo_factory(repo_name: str) -> AbstractUserRepository:
        users = get_users(repo_name)

        return FakeUserRepository(users=users)

    return _user_repo_factory


@pytest.fixture
def create_uow() -> UOWFactory:
    def _uow_factory(repo_name: str) -> AbstractUOW:
        users = get_users(repo_name)

        return FakeUOW(users=users)

    return _uow_factory
