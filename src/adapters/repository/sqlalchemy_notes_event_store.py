from typing import Any, Mapping, Sequence
from uuid import UUID

from sqlalchemy import Row, insert, select
from sqlalchemy.orm import Session

from src.adapters.orm.notes import note_event_table
from src.adapters.repository.notes_event_store import AbstractNoteEventStore
from src.domain.notes import (
    AuthorType,
    EventType,
    NoteCreatedEvent,
    NoteDeletedEvent,
    NoteEvent,
    NoteID,
    NoteUpdatedEvent,
)


def _to_payload(event: NoteEvent) -> dict[str, Any]:
    if isinstance(event, NoteCreatedEvent):
        return {
            "title": event.title,
            "content": event.content,
            "owner": str(event.owner),
        }

    if isinstance(event, NoteUpdatedEvent):
        return {"title": event.title, "content": event.content}

    if isinstance(event, NoteDeletedEvent):
        return {}

    raise ValueError(f"Cannot serialise unsupported note event: {type(event).__name__}")


def _to_row(event: NoteEvent) -> dict[str, Any]:
    return {
        "id": event.id,
        "note_id": event.note_id,
        "event_type": event.event_type.value,
        "timestamp": event.timestamp,
        "author_id": event.author_id,
        "author_type": event.author_type.value,
        "payload": _to_payload(event),
    }


def event_from_dict(data: Mapping[str, Any]) -> NoteEvent:
    """Build an event from a mapping shaped like a note_events row.

    Base fields are expected already coerced: UUIDs as UUID, timestamp as
    datetime. Callers reading JSON coerce before calling.
    """
    event_type = EventType(data["event_type"])
    payload = data["payload"]

    if event_type is EventType.CREATED:
        return NoteCreatedEvent(
            id=data["id"],
            note_id=data["note_id"],
            timestamp=data["timestamp"],
            author_id=data["author_id"],
            author_type=AuthorType(data["author_type"]),
            title=payload["title"],
            content=payload["content"],
            owner=UUID(payload["owner"]),
        )

    if event_type is EventType.UPDATED:
        return NoteUpdatedEvent(
            id=data["id"],
            note_id=data["note_id"],
            timestamp=data["timestamp"],
            author_id=data["author_id"],
            author_type=AuthorType(data["author_type"]),
            title=payload["title"],
            content=payload["content"],
        )

    if event_type is EventType.DELETED:
        return NoteDeletedEvent(
            id=data["id"],
            note_id=data["note_id"],
            timestamp=data["timestamp"],
            author_id=data["author_id"],
            author_type=AuthorType(data["author_type"]),
        )

    raise ValueError(f"Cannot deserialise unsupported note event type: {event_type}")


def event_from_row(row: Row[Any]) -> NoteEvent:
    return event_from_dict(dict(row._mapping))


class SQLAlchemyNoteEventStore(AbstractNoteEventStore):
    _session: Session

    def __init__(self, session: Session):
        self._session = session

    def append(self, events: Sequence[NoteEvent]) -> None:
        if not events:
            return

        self._session.execute(
            insert(note_event_table), [_to_row(event) for event in events]
        )

    def get_events(self, note_id: NoteID) -> Sequence[NoteEvent]:
        rows = self._session.execute(
            select(note_event_table)
            .where(note_event_table.c.note_id == note_id)
            .order_by(note_event_table.c.seq)
        ).all()

        return [event_from_row(row) for row in rows]
