from abc import ABC, abstractmethod

from src.domain.model import Email, NewUser, User, UserID, Username


class AbstractUserRepository(ABC):
    @abstractmethod
    def get(self, offset: int = 0, limit: int = 100) -> list[User]:
        pass

    @abstractmethod
    def create(self, user: NewUser) -> User:
        pass

    @abstractmethod
    def delete(self, user: UserID) -> None:
        pass

    @abstractmethod
    def get_by_id(self, user_id: UserID) -> User | None:
        pass

    @abstractmethod
    def get_by_email(self, email: Email) -> User | None:
        pass

    @abstractmethod
    def get_by_username(self, username: Username) -> User | None:
        pass
