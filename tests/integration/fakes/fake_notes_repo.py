from dataclasses import replace
from typing import Optional, Sequence

from src.adapters.repository import (
    AbstractNoteEventStore,
    AbstractNoteProjection,
    NotesRepository,
)
from src.domain.notes import Note, NoteEvent, NoteID
from src.domain.user import UserID


class FakeNoteEventStore(AbstractNoteEventStore):
    _events: list[NoteEvent]

    def __init__(self, events: Optional[Sequence[NoteEvent]] = None):
        self._events = list(events or [])

    def append(self, events: Sequence[NoteEvent]) -> None:
        self._events.extend(events)

    def get_events(self, note_id: NoteID) -> Sequence[NoteEvent]:
        return [event for event in self._events if event.note_id == note_id]


class FakeNoteProjection(AbstractNoteProjection):
    _notes: dict[NoteID, Note]

    def __init__(self) -> None:
        self._notes = {}

    @classmethod
    def from_events(cls, events: Sequence[NoteEvent]) -> "FakeNoteProjection":
        """Seed the read model by replaying an event log, as a rebuild would."""
        projection = cls()

        streams: dict[NoteID, list[NoteEvent]] = {}
        for event in events:
            streams.setdefault(event.note_id, []).append(event)

        for stream in streams.values():
            projection.upsert(Note.from_events(stream))

        return projection

    def upsert(self, note: Note) -> None:
        self._notes[note.id] = replace(note, _events=[])

    def get_by_owner(self, owner: UserID) -> Sequence[Note]:
        return sorted(
            (
                note
                for note in self._notes.values()
                if note.owner == owner and not note.deleted
            ),
            key=lambda note: note.last_updated,
            reverse=True,
        )


def create_fake_notes_repo(
    events: Optional[Sequence[NoteEvent]] = None,
) -> NotesRepository:
    return NotesRepository(
        FakeNoteEventStore(events), FakeNoteProjection.from_events(events or [])
    )
