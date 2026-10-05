from typing import Optional

from src.adapters import AbstractUserRepository
from src.domain.user import Email, NewUser, User, UserID, Username


class FakeUserRepository(AbstractUserRepository):
    _users: list[User]

    def __init__(self, users: Optional[list[User]] = None):
        super().__init__()

        self._users = users or []

    def get(self, offset: int = 0, limit: int = 100) -> list[User]:
        return self._users[offset : offset + limit]

    def create(self, user: NewUser) -> User:
        new_user = User.register(user)
        self._users.append(new_user)

        return new_user

    def delete(self, user: UserID) -> None:
        self._users = [u for u in self._users if u.id != user]

    def get_by_id(self, user_id: UserID) -> User | None:
        return next((u for u in self._users if u.id == user_id), None)

    def get_by_email(self, email: Email) -> User | None:
        return next((u for u in self._users if u.email == email), None)

    def get_by_username(self, username: Username) -> User | None:
        return next((u for u in self._users if u.username == username), None)
