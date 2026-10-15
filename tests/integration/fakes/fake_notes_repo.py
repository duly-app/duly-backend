from dataclasses import replace
from datetime import datetime
from typing import Optional, Sequence

from src.adapters.repository import (
    AbstractNoteEventStore,
    AbstractNoteProjection,
    NoteOrder,
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

    def search(self, owner: UserID, query: str, limit: int) -> Sequence[Note]:
        """Substring matching, ANDed across words.

        Postgres stems and ranks; this cannot. The AND semantics match
        websearch_to_tsquery's default, so the shape of a query behaves the
        same, but results come back by recency rather than relevance.
        """
        words = query.lower().split()

        def matches(note: Note) -> bool:
            haystack = f"{note.title}\n{note.content}".lower()

            return all(word in haystack for word in words)

        return [note for note in self.get_by_owner(owner) if matches(note)][:limit]

    def get_by_owner(
        self,
        owner: UserID,
        order_by: NoteOrder = NoteOrder.LAST_UPDATED,
        descending: bool = True,
        updated_after: datetime | None = None,
        updated_before: datetime | None = None,
    ) -> Sequence[Note]:
        def in_window(note: Note) -> bool:
            if updated_after is not None and note.last_updated < updated_after:
                return False

            return updated_before is None or note.last_updated < updated_before

        return sorted(
            (
                note
                for note in self._notes.values()
                if note.owner == owner and not note.deleted and in_window(note)
            ),
            key=lambda note: (getattr(note, order_by.value), str(note.id)),
            reverse=descending,
        )


def create_fake_notes_repo(
    events: Optional[Sequence[NoteEvent]] = None,
) -> NotesRepository:
    return NotesRepository(
        FakeNoteEventStore(events), FakeNoteProjection.from_events(events or [])
    )
