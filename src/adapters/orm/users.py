from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Dialect,
    ForeignKey,
    Integer,
    String,
    Table,
    Uuid,
    types,
)

from src.adapters.orm.base import metadata
from src.domain.roles import Role
from src.domain.user import Email, Username


class RoleType(types.TypeDecorator[Role]):
    impl = Integer
    cache_ok = True

    def process_bind_param(self, value: Role | None, dialect: Dialect) -> int | None:
        if value is None:
            return None

        return int(value)

    def process_result_value(self, value: int | None, dialect: Dialect) -> Role | None:
        if value is not None:
            return Role(value)

        return None


class UsernameType(types.TypeDecorator[Username]):
    impl = String(50)
    cache_ok = True

    def process_bind_param(
        self, value: Username | None, dialect: Dialect
    ) -> str | None:
        if value is None:
            return None

        return value.value

    def process_result_value(
        self, value: str | None, dialect: Dialect
    ) -> Username | None:
        if value is not None:
            return Username(value)

        return None


class EmailType(types.TypeDecorator[Email]):
    impl = String(100)
    cache_ok = True

    def process_bind_param(self, value: Email | None, dialect: Dialect) -> str | None:
        if value is None:
            return None

        return value.value

    def process_result_value(self, value: str | None, dialect: Dialect) -> Email | None:
        if value is not None:
            return Email(value)

        return None


role_table = Table(
    "roles",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("name", String(50), nullable=False, unique=True),
)


user_table = Table(
    "users",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("username", UsernameType, nullable=False, unique=True),
    Column("email", EmailType, nullable=False, unique=True),
    Column("password_hash", String(255), nullable=False),
    Column("created_at", DateTime, nullable=False),
    Column("verified", Boolean, nullable=False, default=False),
    Column("role_id", RoleType, ForeignKey("roles.id"), nullable=False),
)
