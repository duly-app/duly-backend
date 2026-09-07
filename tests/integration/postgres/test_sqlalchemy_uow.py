from sqlalchemy.orm import Session, sessionmaker

from src.domain.model import Email, NewUser, Username
from src.service.uow import SQLAlchemyUOW


class TestSQLAlchemyUOW:
    def test_commit_persists_the_created_user(
        self, session_factory: sessionmaker[Session]
    ):
        new_user = NewUser(
            email=Email("committed@test.com"),
            username=Username("committed_user"),
            password_hash="hashed_password",
        )

        with SQLAlchemyUOW(session_factory) as uow:
            created = uow.users.create(new_user)
            uow.commit()

            fetched = uow.users.get_by_id(created.id)

            assert fetched is not None
            assert fetched.username == Username("committed_user")
            assert fetched.email == Email("committed@test.com")

    def test_rollback_discards_the_created_user(
        self, session_factory: sessionmaker[Session]
    ):
        new_user = NewUser(
            email=Email("rolled_back@test.com"),
            username=Username("rolled_back_user"),
            password_hash="hashed_password",
        )

        with SQLAlchemyUOW(session_factory) as uow:
            created = uow.users.create(new_user)
            created_id = created.id
            uow.rollback()

        with SQLAlchemyUOW(session_factory) as verifying_uow:
            assert verifying_uow.users.get_by_id(created_id) is None

    def test_exiting_without_commit_discards_changes(
        self, session_factory: sessionmaker[Session]
    ):
        new_user = NewUser(
            email=Email("uncommitted@test.com"),
            username=Username("uncommitted_user"),
            password_hash="hashed_password",
        )

        with SQLAlchemyUOW(session_factory) as uow:
            created = uow.users.create(new_user)
            created_id = created.id

        with SQLAlchemyUOW(session_factory) as verifying_uow:
            assert verifying_uow.users.get_by_id(created_id) is None
