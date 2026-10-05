from abc import ABC
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import TypeAlias, Union
from uuid import UUID, uuid4

from src.domain.notes_errors import (
    NoteAlreadyDeletedError,
    NoteAlreadyExistsError,
    NoteIdMismatchError,
    NoteTimestampError,
    NoUpdateDeletedNoteError,
)
from src.domain.user import UserID

NoteID: TypeAlias = UUID


class EventType(StrEnum):
    CREATED = "created"
    UPDATED = "updated"
    DELETED = "deleted"


class AuthorType(StrEnum):
    SYSTEM = "system"
    USER = "user"
    AI = "ai"


@dataclass(frozen=True, kw_only=True)
class NoteEventBase(ABC):
    id: UUID
    note_id: NoteID
    event_type: EventType
    timestamp: datetime
    author_id: UserID
    author_type: AuthorType


@dataclass(frozen=True, kw_only=True)
class NoteCreatedEvent(NoteEventBase):
    title: str
    content: str
    owner: UserID
    event_type: EventType = EventType.CREATED


@dataclass(frozen=True, kw_only=True)
class NoteUpdatedEvent(NoteEventBase):
    title: str
    content: str
    event_type: EventType = EventType.UPDATED


@dataclass(frozen=True, kw_only=True)
class NoteDeletedEvent(NoteEventBase):
    event_type: EventType = EventType.DELETED


NoteEvent: TypeAlias = Union[NoteCreatedEvent, NoteUpdatedEvent, NoteDeletedEvent]


@dataclass
class Note:
    id: NoteID
    title: str
    content: str
    created_at: datetime
    last_updated: datetime
    updated_by: UserID
    last_author_type: AuthorType
    owner: UserID
    deleted: bool = field(default=False)
    version: int = field(default=0)
    _events: list[NoteEvent] = field(default_factory=list, repr=False, compare=False)

    @property
    def events(self) -> list[NoteEvent]:
        return list(self._events)

    def clear_events(self) -> None:
        self._events.clear()

    @classmethod
    def create(
        cls,
        title: str,
        content: str,
        owner: UserID,
        author_id: UserID | None = None,
        author_type: AuthorType = AuthorType.USER,
        timestamp: datetime | None = None,
        note_id: NoteID | None = None,
        event_id: UUID | None = None,
    ) -> "Note":
        now = timestamp or datetime.now(timezone.utc)
        note_id_ = note_id or uuid4()
        author_id_ = author_id or owner

        event = NoteCreatedEvent(
            id=event_id or uuid4(),
            note_id=note_id_,
            timestamp=now,
            author_id=author_id_,
            author_type=author_type,
            title=title,
            content=content,
            owner=owner,
        )

        note = cls(
            id=note_id_,
            title=title,
            content=content,
            created_at=now,
            last_updated=now,
            updated_by=author_id_,
            last_author_type=author_type,
            owner=owner,
            deleted=False,
            version=0,
        )
        note._apply_and_record(event)

        return note

    def update(
        self,
        title: str,
        content: str,
        author_id: UserID,
        author_type: AuthorType = AuthorType.USER,
        timestamp: datetime | None = None,
        event_id: UUID | None = None,
    ) -> None:
        if self.deleted:
            raise NoUpdateDeletedNoteError("Cannot update a deleted note.")

        if self.title == title and self.content == content:
            return

        event = NoteUpdatedEvent(
            id=event_id or uuid4(),
            note_id=self.id,
            title=title,
            content=content,
            timestamp=timestamp or datetime.now(timezone.utc),
            author_id=author_id,
            author_type=author_type,
        )
        self._apply_and_record(event)

    def delete(
        self,
        author_id: UserID,
        author_type: AuthorType = AuthorType.USER,
        timestamp: datetime | None = None,
        event_id: UUID | None = None,
    ) -> None:
        if self.deleted:
            raise NoteAlreadyDeletedError("Cannot delete an already deleted note.")

        event = NoteDeletedEvent(
            id=event_id or uuid4(),
            note_id=self.id,
            timestamp=timestamp or datetime.now(timezone.utc),
            author_id=author_id,
            author_type=author_type,
        )
        self._apply_and_record(event)

    def _apply_and_record(self, event: NoteEvent) -> None:
        self.apply(event)
        self._events.append(event)

    def _validate_event(self, event: NoteEvent) -> None:
        if event.note_id != self.id:
            raise NoteIdMismatchError(
                f"Event note_id {event.note_id} does not match Note id {self.id}"
            )

        if event.timestamp < self.last_updated:
            raise NoteTimestampError(
                f"Event timestamp {event.timestamp} is earlier than last_updated \
{self.last_updated}"
            )

        if event.event_type == EventType.CREATED and self.version > 0:
            raise NoteAlreadyExistsError(
                "Cannot apply a create event to an existing note."
            )

        if event.event_type == EventType.UPDATED and self.deleted:
            raise NoteAlreadyDeletedError(
                "Cannot apply an update event to a deleted note."
            )

        if event.event_type == EventType.DELETED and self.deleted:
            raise NoteAlreadyDeletedError(
                "Cannot apply a delete event to an already deleted note."
            )

    def apply(self, event: NoteEvent) -> None:
        self.version += 1
        self.last_updated = event.timestamp
        self.updated_by = event.author_id
        self.last_author_type = event.author_type

        if isinstance(event, NoteCreatedEvent):
            self.id = event.note_id
            self.title = event.title
            self.content = event.content
            self.created_at = event.timestamp
            self.owner = event.owner
            self.deleted = False
        elif isinstance(event, NoteUpdatedEvent):
            self.title = event.title
            self.content = event.content
        elif isinstance(event, NoteDeletedEvent):
            self.deleted = True

    @classmethod
    def from_events(cls, events: Iterable[NoteEvent]) -> "Note":
        event_iter = iter(events)

        try:
            first_event = next(event_iter)
        except StopIteration as err:
            raise ValueError(
                "Cannot instantiate Note from an empty event stream."
            ) from err

        if not isinstance(first_event, NoteCreatedEvent):
            raise ValueError(f"First event must be NoteCreatedEvent, \
got {type(first_event).__name__}")

        note = cls(
            id=first_event.note_id,
            title="",
            content="",
            created_at=first_event.timestamp,
            last_updated=first_event.timestamp,
            updated_by=first_event.author_id,
            last_author_type=first_event.author_type,
            owner=first_event.owner,
            deleted=False,
            version=0,
        )
        note.apply(first_event)

        for event in event_iter:
            note._validate_event(event)

            note.apply(event)

        return note
