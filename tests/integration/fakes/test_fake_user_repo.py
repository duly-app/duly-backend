from uuid import UUID

from src.domain.user import Email, Username
from tests.integration.conftest import UserRepoFactory


def test_loads_correct_number_of_users(create_user_repo: UserRepoFactory):
    repo = create_user_repo("test_repo")

    assert len(repo.get(0, 100)) == 2


def test_users_are_retrievable_by_email(create_user_repo: UserRepoFactory):
    repo = create_user_repo("test_repo")
    user = repo.get_by_email(Email("user_one@test.com"))

    assert user is not None
    assert user.username == Username("user_one")


def test_users_are_retrievable_by_id(create_user_repo: UserRepoFactory):
    repo = create_user_repo("test_repo")
    user = repo.get_by_id(UUID("00000000-0000-0000-0000-000000000002"))

    assert user is not None
    assert user.email == Email("user_two@test.com")
