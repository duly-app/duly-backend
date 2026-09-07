from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from src.domain.model import Email, NewUser, User, UserID, Username


class AbstractUserRepository(ABC):
    @abstractmethod
    def get(self, offset: int = 0, limit: int = 100) -> list[User]:
        raise NotImplementedError

    @abstractmethod
    def create(self, user: NewUser) -> User:
        raise NotImplementedError

    @abstractmethod
    def delete(self, user: UserID) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_by_id(self, user_id: UserID) -> User | None:
        raise NotImplementedError

    @abstractmethod
    def get_by_email(self, email: Email) -> User | None:
        raise NotImplementedError

    @abstractmethod
    def get_by_username(self, username: Username) -> User | None:
        raise NotImplementedError


class SQLAlchemyUserRepository(AbstractUserRepository):
    _session: Session

    def __init__(self, session: Session):
        self._session = session

    def get(self, offset: int = 0, limit: int = 100) -> list[User]:
        return self._session.query(User).offset(offset).limit(limit).all()

    def create(self, user: NewUser) -> User:
        new_user = User.register(user)

        self._session.add(new_user)

        result = self.get_by_username(new_user.username)

        if result is None:
            raise ValueError(f"User with username {user.username} was not created.")

        return result

    def delete(self, user: UserID) -> None:
        match = self._session.query(User).filter_by(id=user).first()

        if match:
            self._session.delete(match)

        return

    def get_by_id(self, user_id: UserID) -> User | None:
        return self._session.query(User).filter_by(id=user_id).first()

    def get_by_email(self, email: Email) -> User | None:
        return self._session.query(User).filter_by(email=email).first()

    def get_by_username(self, username: Username) -> User | None:
        return self._session.query(User).filter_by(username=username).first()
