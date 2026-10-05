from abc import ABC, abstractmethod
from typing import Sequence

from src.domain.notes import Note
from src.domain.user import UserID


class AbstractNoteProjection(ABC):
    """Read model over the note event log. Derived state, never a source of truth."""

    @abstractmethod
    def upsert(self, note: Note) -> None:
        """Write the current state of a note into the read model."""

    @abstractmethod
    def get_by_owner(self, owner: UserID) -> Sequence[Note]:
        """Retrieve every note owned by a user, excluding deleted ones."""
