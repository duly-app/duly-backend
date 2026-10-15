from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Sequence

from src.domain.notes import Note
from src.domain.user import UserID


class NoteOrder(str, Enum):
    """What a listing can be sorted by."""

    LAST_UPDATED = "last_updated"
    CREATED_AT = "created_at"
    TITLE = "title"


class AbstractNoteProjection(ABC):
    """Read model over the note event log. Derived state, never a source of truth."""

    @abstractmethod
    def upsert(self, note: Note) -> None:
        """Write the current state of a note into the read model."""

    @abstractmethod
    def get_by_owner(
        self,
        owner: UserID,
        order_by: NoteOrder = NoteOrder.LAST_UPDATED,
        descending: bool = True,
        updated_after: datetime | None = None,
        updated_before: datetime | None = None,
    ) -> Sequence[Note]:
        """A user's notes, excluding deleted ones."""

    @abstractmethod
    def search(self, owner: UserID, query: str, limit: int) -> Sequence[Note]:
        """A user's notes matching a free-text query, best matches first."""
