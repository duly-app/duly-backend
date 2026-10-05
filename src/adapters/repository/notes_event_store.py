from abc import ABC, abstractmethod
from typing import Sequence

from src.domain.notes import NoteEvent, NoteID


class AbstractNoteEventStore(ABC):
    @abstractmethod
    def append(self, events: Sequence[NoteEvent]) -> None:
        """Append a list of events for a note to the event store."""

    @abstractmethod
    def get_events(self, note_id: NoteID) -> Sequence[NoteEvent]:
        """Retrieve all events for a given note from the event store."""
