from uuid import UUID

import pytest

from src.domain.notes import AuthorType, Note, NoteCreatedEvent, NoteEvent
from src.domain.notes_errors import (
    NoteAlreadyDeletedError,
    NoteAlreadyExistsError,
    NoteIdMismatchError,
    NoteTimestampError,
    NoUpdateDeletedNoteError,
)
from tests.unit.src.domain.model.conftest import NoteEventFactories

OWNER_ID = UUID("00000000-0000-0000-0000-000000000001")


def test_creating_a_note_applies_creation_event():
    note = Note.create(
        title="Test Note",
        content="This is a test note.",
        owner=OWNER_ID,
    )

    assert isinstance(note, Note)
    assert len(note.events) == 1
    assert isinstance(note.events[0], NoteCreatedEvent)


def test_expected_note_from_event_list(note_event_factories: NoteEventFactories):
    note_id = UUID("00000000-0000-0000-0000-000000000001")

    events: list[NoteEvent] = [
        note_event_factories["note_created"](note_id=note_id, title="First"),
        note_event_factories["note_updated"](note_id=note_id, title="Second"),
        note_event_factories["note_updated"](note_id=note_id, title="Third"),
    ]

    note_from_events = Note.from_events(events)

    assert note_from_events.title == "Third"
    assert note_from_events.version == len(events)
    # Replayed history is already persisted; it must not be re-queued for saving.
    assert note_from_events.events == []


def test_cannot_delete_deleted_note():
    note = Note.create(title="Test Note", content="Original", owner=OWNER_ID)
    note.delete(author_id=OWNER_ID)

    with pytest.raises(NoteAlreadyDeletedError):
        note.delete(author_id=OWNER_ID)


def test_update_with_unchanged_title_and_content_is_a_no_op():
    note = Note.create(title="Test Note", content="Original", owner=OWNER_ID)
    note.clear_events()
    version_before = note.version

    note.update(title="Test Note", content="Original", author_id=OWNER_ID)

    assert note.version == version_before
    assert note.events == []


def test_events_property_returns_a_defensive_copy():
    note = Note.create(title="Test Note", content="Original", owner=OWNER_ID)

    returned_events = note.events
    returned_events.clear()

    assert len(note.events) == 1


def test_clear_events_empties_pending_events_without_affecting_state():
    note = Note.create(title="Test Note", content="Original", owner=OWNER_ID)
    note.update(title="Updated", content="Updated", author_id=OWNER_ID)

    note.clear_events()

    assert note.events == []
    assert note.title == "Updated"
    assert note.version == 2


def test_update_records_ai_authorship_distinct_from_owner():
    note = Note.create(title="Test Note", content="Original", owner=OWNER_ID)
    ai_agent_id = UUID("00000000-0000-0000-0000-000000000099")

    note.update(
        title="AI Rewrite",
        content="Rewritten by AI",
        author_id=ai_agent_id,
        author_type=AuthorType.AI,
    )

    assert note.updated_by == ai_agent_id
    assert note.last_author_type == AuthorType.AI
    assert note.owner == OWNER_ID


def test_cannot_update_deleted_note():
    note = Note.create(title="Test Note", content="Original", owner=OWNER_ID)
    note.delete(author_id=OWNER_ID)

    with pytest.raises(NoUpdateDeletedNoteError):
        note.update(
            title="Updated Title", content="Updated content.", author_id=OWNER_ID
        )


def test_from_events_rejects_an_empty_stream():
    with pytest.raises(ValueError):
        Note.from_events([])


def test_from_events_requires_a_creation_event_first(
    note_event_factories: NoteEventFactories,
):
    with pytest.raises(ValueError):
        Note.from_events([note_event_factories["note_updated"]()])


def test_from_events_rejects_a_duplicate_creation_event(
    note_event_factories: NoteEventFactories,
):
    note_id = UUID("00000000-0000-0000-0000-000000000001")

    events = [
        note_event_factories["note_created"](note_id=note_id),
        note_event_factories["note_created"](note_id=note_id),
    ]

    with pytest.raises(NoteAlreadyExistsError):
        Note.from_events(events)


def test_from_events_rejects_an_event_for_a_different_note(
    note_event_factories: NoteEventFactories,
):
    note_id = UUID("00000000-0000-0000-0000-000000000001")
    other_note_id = UUID("00000000-0000-0000-0000-000000000002")

    events: list[NoteEvent] = [
        note_event_factories["note_created"](note_id=note_id),
        note_event_factories["note_updated"](note_id=other_note_id),
    ]

    with pytest.raises(NoteIdMismatchError):
        Note.from_events(events)


def test_from_events_rejects_out_of_order_timestamps(
    note_event_factories: NoteEventFactories,
):
    from datetime import datetime, timedelta, timezone

    note_id = UUID("00000000-0000-0000-0000-000000000001")
    created_at = datetime.now(timezone.utc)
    earlier = created_at - timedelta(seconds=1)

    events: list[NoteEvent] = [
        note_event_factories["note_created"](note_id=note_id, timestamp=created_at),
        note_event_factories["note_updated"](note_id=note_id, timestamp=earlier),
    ]

    with pytest.raises(NoteTimestampError):
        Note.from_events(events)


def test_from_events_rejects_update_after_delete(
    note_event_factories: NoteEventFactories,
):
    note_id = UUID("00000000-0000-0000-0000-000000000001")

    events: list[NoteEvent] = [
        note_event_factories["note_created"](note_id=note_id),
        note_event_factories["note_deleted"](note_id=note_id),
        note_event_factories["note_updated"](note_id=note_id),
    ]

    with pytest.raises(NoteAlreadyDeletedError):
        Note.from_events(events)
