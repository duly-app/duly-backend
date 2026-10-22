from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from src.adapters.orm.notes import note_embedding_table
from src.adapters.repository.note_embeddings import fetch_pending_notes, store_embedding
from src.adapters.repository.sqlalchemy_notes_projection import (
    SQLAlchemyNoteProjection,
)
from src.domain.notes import AuthorType, Note, NoteID
from src.service.sweeper import sweep_once
from tests.integration.fakes.fake_embedder import FakeEmbedder, vector

OWNER = UUID("550e8400-e29b-41d4-a716-446655440099")

NOW = datetime(2026, 10, 18, 12, 0, tzinfo=timezone.utc)


def note(
    title: str,
    content: str,
    version: int = 0,
    deleted: bool = False,
    note_id: NoteID | None = None,
) -> Note:
    return Note(
        id=note_id or uuid4(),
        title=title,
        content=content,
        created_at=NOW,
        last_updated=NOW,
        updated_by=OWNER,
        last_author_type=AuthorType.USER,
        owner=OWNER,
        deleted=deleted,
        version=version,
    )


def text_of(each: Note) -> str:
    """What the sweeper hands the embedder, per PendingNote.text."""
    return f"{each.title}\n\n{each.content}"


def write(session: Session, *notes: Note) -> None:
    projection = SQLAlchemyNoteProjection(session)

    for each in notes:
        projection.upsert(each)


def stored_embedding(session: Session, note_id: NoteID) -> list[float] | None:
    row = session.execute(
        select(
            note_embedding_table.c.note_version,
            note_embedding_table.c.embedding,
        ).where(note_embedding_table.c.note_id == note_id)
    ).one_or_none()

    return None if row is None else [float(value) for value in row.embedding]


def stored_version(session: Session, note_id: NoteID) -> int | None:
    return session.scalar(
        select(note_embedding_table.c.note_version).where(
            note_embedding_table.c.note_id == note_id
        )
    )


class TestPending:
    def test_a_note_without_an_embedding_is_pending(
        self, session_factory: sessionmaker[Session]
    ):
        with session_factory() as session:
            waiting = note("Sourdough", "Fed the starter.")
            write(session, waiting)

            assert [each.id for each in fetch_pending_notes(session, limit=10)] == [
                waiting.id
            ]

    def test_a_deleted_note_is_not_pending(
        self, session_factory: sessionmaker[Session]
    ):
        with session_factory() as session:
            write(session, note("Gone", "Removed.", deleted=True))

            assert fetch_pending_notes(session, limit=10) == []

    def test_an_embedded_note_is_not_pending(
        self, session_factory: sessionmaker[Session]
    ):
        with session_factory() as session:
            embedded = note("Pasta", "100g flour to one egg.")
            write(session, embedded)

            assert store_embedding(session, embedded.id, embedded.version, vector(0.5))
            assert fetch_pending_notes(session, limit=10) == []

    def test_pending_is_capped_by_the_limit(
        self, session_factory: sessionmaker[Session]
    ):
        with session_factory() as session:
            write(session, *(note(f"Note {index}", "Text.") for index in range(5)))

            assert len(fetch_pending_notes(session, limit=2)) == 2


class TestSweepOnce:
    def test_it_stores_the_vector_the_embedder_returned(
        self, session_factory: sessionmaker[Session]
    ):
        with session_factory() as session:
            waiting = note("Sourdough", "Fed the starter.")
            write(session, waiting)
            session.commit()

        embedder = FakeEmbedder({text_of(waiting): vector(0.25)})

        assert sweep_once(session_factory, embedder) == 1

        with session_factory() as session:
            assert stored_embedding(session, waiting.id) == vector(0.25)
            assert stored_version(session, waiting.id) == 0

    def test_it_embeds_the_whole_batch_in_one_call(
        self, session_factory: sessionmaker[Session]
    ):
        with session_factory() as session:
            write(session, *(note(f"Note {index}", "Text.") for index in range(3)))
            session.commit()

        embedder = FakeEmbedder()

        assert sweep_once(session_factory, embedder) == 3
        assert len(embedder.calls) == 1
        assert len(embedder.calls[0]) == 3

    def test_it_does_nothing_when_there_is_nothing_to_embed(
        self, session_factory: sessionmaker[Session]
    ):
        embedder = FakeEmbedder()

        assert sweep_once(session_factory, embedder) == 0
        assert embedder.calls == []

    def test_it_leaves_the_notes_alone_when_the_embedder_is_not_ready(
        self, session_factory: sessionmaker[Session]
    ):
        with session_factory() as session:
            waiting = note("Sourdough", "Fed the starter.")
            write(session, waiting)
            session.commit()

        embedder = FakeEmbedder(ready=False)

        assert sweep_once(session_factory, embedder) == 0
        assert embedder.calls == []

        with session_factory() as session:
            assert stored_embedding(session, waiting.id) is None
            assert fetch_pending_notes(session, limit=10)

    def test_a_note_edited_while_being_embedded_keeps_no_stale_vector(
        self, session_factory: sessionmaker[Session]
    ):
        # The race the version guard exists for: the sweep reads version 0,
        # the user edits to version 1, and the vector describing the old text
        # must not be attached to the new one.
        with session_factory() as session:
            original = note("Sourdough", "Fed the starter.")
            write(session, original)

            read_at = fetch_pending_notes(session, limit=10)[0]

            write(
                session,
                note(
                    "Sourdough",
                    "Fed the rye starter.",
                    version=1,
                    note_id=original.id,
                ),
            )

            assert not store_embedding(
                session, read_at.id, read_at.version, vector(0.75)
            )
            assert stored_embedding(session, original.id) is None

            # Still waiting, so the next sweep embeds the new text.
            assert [each.id for each in fetch_pending_notes(session, limit=10)] == [
                original.id
            ]
