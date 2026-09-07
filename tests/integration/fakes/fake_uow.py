from typing import Optional

from src.domain import User
from src.service.uow import AbstractUOW
from tests.integration.fakes.fake_user_repo import FakeUserRepository


class FakeUOW(AbstractUOW):
    def __init__(self, users: Optional[list[User]] = None):
        self.users = FakeUserRepository(users)

    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        pass
