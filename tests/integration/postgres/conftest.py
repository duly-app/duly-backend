from collections.abc import Iterator

import pytest
from sqlalchemy import Connection, Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.adapters.orm import metadata, role_table, start_mappers
from src.domain.roles import Role
from src.environment import EnvVar, load_env_vars

# .env.dev's TEST_DATABASE_URL points at the "duly-postgres" docker network hostname,
# which only resolves inside the docker network (e.g., when running the suite inside
# dev-duly-backend container, or in CI). It's unset on a bare host, so fall back to the
# port that docker-compose.dev.yml forwards to localhost.
TEST_DATABASE_URL = load_env_vars()[EnvVar.TEST_DATABASE_URL] or (
    "postgresql+psycopg2://admin:password@localhost:5432/duly_test"
)


@pytest.fixture(scope="class")
def postgres_engine() -> Iterator[Engine]:
    """Creates the schema once per test class and tears it down after.

    Requires a running Postgres reachable at TEST_DATABASE_URL (see
    docker-compose.dev.yml's duly-postgres service / duly_test database).
    """
    start_mappers()

    engine = create_engine(TEST_DATABASE_URL)
    metadata.create_all(engine)

    with engine.begin() as connection:
        connection.execute(
            role_table.insert(),
            [{"id": role.value, "name": role.name} for role in Role],
        )

    yield engine

    metadata.drop_all(engine)
    engine.dispose()


@pytest.fixture
def postgres_connection(postgres_engine: Engine) -> Iterator[Connection]:
    """Opens one transaction per test and rolls it back afterwards.

    Kept as a standalone fixture (not a class method) so any test class can
    reuse it against a fresh, isolated transaction without touching the
    class-scoped schema.
    """
    connection = postgres_engine.connect()
    transaction = connection.begin()

    yield connection

    transaction.rollback()
    connection.close()


@pytest.fixture
def session_factory(postgres_connection: Connection) -> sessionmaker[Session]:
    """A sessionmaker bound to the per-test transaction.

    join_transaction_mode="create_savepoint" means Session.commit() only
    releases a SAVEPOINT instead of ending the outer transaction, so
    committed data stays visible within the test but never survives it.
    """
    return sessionmaker(
        bind=postgres_connection, join_transaction_mode="create_savepoint"
    )
