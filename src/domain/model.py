import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TypeAlias
from uuid import UUID, uuid4

from src.domain.exceptions import InvalidEmailError, InvalidUsernameError
from src.domain.roles import Role

EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")


UserID: TypeAlias = UUID
PassWordHash: TypeAlias = str


@dataclass(frozen=True)
class Username:
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise InvalidUsernameError("Username cannot be empty")


@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self):
        if not EMAIL_REGEX.match(self.value):
            raise InvalidEmailError(f"Invalid email address: {self.value}")


@dataclass(frozen=True)
class NewUser:
    email: Email
    username: Username
    password_hash: PassWordHash

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NewUser):
            return NotImplemented

        return self.email == other.email and self.username == other.username

    def __hash__(self) -> int:
        return hash((self.email, self.username))


@dataclass
class User:
    id: UserID
    username: Username
    email: Email
    password_hash: PassWordHash
    created_at: datetime
    verified: bool
    role: Role

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, User):
            return NotImplemented

        return self.id == other.id

    def __hash__(self) -> int:
        return hash(self.id)

    @classmethod
    def register(cls, new_user: NewUser, role: Role = Role.USER) -> "User":
        return cls(
            id=uuid4(),
            username=new_user.username,
            email=new_user.email,
            password_hash=new_user.password_hash,
            created_at=datetime.now(timezone.utc),
            verified=False,
            role=role,
        )
