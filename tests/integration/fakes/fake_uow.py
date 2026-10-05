from typing import Optional, Sequence

from src.domain import User
from src.domain.notes import NoteEvent
from src.service.uow import AbstractUOW
from tests.integration.fakes.fake_notes_repo import create_fake_notes_repo
from tests.integration.fakes.fake_user_repo import FakeUserRepository


class FakeUOW(AbstractUOW):
    def __init__(
        self,
        users: Optional[list[User]] = None,
        note_events: Optional[Sequence[NoteEvent]] = None,
    ):
        self.users = FakeUserRepository(users)
        self.notes = create_fake_notes_repo(note_events)

    def commit(self) -> None:
        pass

    def rollback(self) -> None:
        pass

    def check_health(self) -> None:
        pass
