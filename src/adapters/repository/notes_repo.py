from typing import Sequence

from src.adapters.repository.notes_event_store import AbstractNoteEventStore
from src.adapters.repository.notes_projection import AbstractNoteProjection
from src.domain.notes import Note, NoteID
from src.domain.user import UserID


class NotesRepository:
    _event_store: AbstractNoteEventStore
    _projection: AbstractNoteProjection

    def __init__(
        self,
        event_store: AbstractNoteEventStore,
        projection: AbstractNoteProjection,
    ):
        self._event_store = event_store
        self._projection = projection

    def get_by_id(self, note_id: NoteID) -> Note | None:
        events = self._event_store.get_events(note_id)

        if not events:
            return None

        return Note.from_events(events)

    def get_by_owner(self, owner: UserID) -> Sequence[Note]:
        return self._projection.get_by_owner(owner)

    def save(self, note: Note) -> None:
        if not note.events:
            return

        self._event_store.append(note.events)
        self._projection.upsert(note)
        note.clear_events()
