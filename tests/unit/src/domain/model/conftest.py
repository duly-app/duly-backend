from datetime import datetime, timezone
from typing import Generic, Protocol, TypeAlias, TypedDict, TypeVar
from uuid import uuid4

import pytest

from src.domain.notes import (
    AuthorType,
    NoteCreatedEvent,
    NoteDeletedEvent,
    NoteEvent,
    NoteUpdatedEvent,
)

T = TypeVar("T", bound=NoteEvent, covariant=True)


class NoteEventFactory(Protocol, Generic[T]):
    def __call__(self, **kwargs) -> T: ...


NoteCreatedEventFactory: TypeAlias = NoteEventFactory[NoteCreatedEvent]
NoteUpdatedEventFactory: TypeAlias = NoteEventFactory[NoteUpdatedEvent]
NoteDeletedEventFactory: TypeAlias = NoteEventFactory[NoteDeletedEvent]


def make_note_created_event(**kwargs) -> NoteCreatedEvent:
    defaults = {
        "id": uuid4(),
        "note_id": uuid4(),
        "timestamp": datetime.now(timezone.utc),
        "author_id": uuid4(),
        "author_type": AuthorType.USER,
        "owner": uuid4(),
        "title": "Sample Title",
        "content": "Sample Content",
    }
    return NoteCreatedEvent(**(defaults | kwargs))  # type: ignore


def make_note_updated_event(**kwargs) -> NoteUpdatedEvent:
    defaults = {
        "id": uuid4(),
        "note_id": uuid4(),
        "timestamp": datetime.now(timezone.utc),
        "author_id": uuid4(),
        "author_type": AuthorType.USER,
        "title": "Updated Title",
        "content": "Updated Content",
    }
    return NoteUpdatedEvent(**(defaults | kwargs))  # type: ignore


def make_note_deleted_event(**kwargs) -> NoteDeletedEvent:
    defaults = {
        "id": uuid4(),
        "note_id": uuid4(),
        "timestamp": datetime.now(timezone.utc),
        "author_id": uuid4(),
        "author_type": AuthorType.USER,
    }
    return NoteDeletedEvent(**(defaults | kwargs))  # type: ignore


class NoteEventFactories(TypedDict):
    note_created: NoteCreatedEventFactory
    note_updated: NoteUpdatedEventFactory
    note_deleted: NoteDeletedEventFactory


@pytest.fixture
def note_created_event_factory() -> NoteCreatedEventFactory:
    return make_note_created_event


@pytest.fixture
def note_updated_event_factory() -> NoteUpdatedEventFactory:
    return make_note_updated_event


@pytest.fixture
def note_deleted_event_factory() -> NoteDeletedEventFactory:
    return make_note_deleted_event


@pytest.fixture
def note_event_factories() -> NoteEventFactories:
    return NoteEventFactories(
        note_created=make_note_created_event,
        note_updated=make_note_updated_event,
        note_deleted=make_note_deleted_event,
    )
