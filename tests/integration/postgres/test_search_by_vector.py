from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlalchemy.orm import Session, sessionmaker

from src.adapters.orm.notes import EMBEDDING_DIMENSIONS, note_embedding_table
from src.adapters.repository.sqlalchemy_notes_projection import (
    SQLAlchemyNoteProjection,
)
from src.domain.notes import AuthorType, Note, NoteID

OWNER = UUID("550e8400-e29b-41d4-a716-446655440099")
STRANGER = UUID("550e8400-e29b-41d4-a716-446655440098")

NOW = datetime(2026, 10, 18, 12, 0, tzinfo=timezone.utc)


def plane(x: float, y: float) -> list[float]:
    """A vector in the first two dimensions, so distances are hand-checkable."""
    return [x, y] + [0.0] * (EMBEDDING_DIMENSIONS - 2)


HERE = plane(1.0, 0.0)
NEARBY = plane(0.8, 0.6)
ELSEWHERE = plane(0.0, 1.0)


def note(title: str, owner: UUID = OWNER, deleted: bool = False) -> Note:
    return Note(
        id=uuid4(),
        title=title,
        content="Text.",
        created_at=NOW,
        last_updated=NOW,
        updated_by=owner,
        last_author_type=AuthorType.USER,
        owner=owner,
        deleted=deleted,
        version=0,
    )


def embed(session: Session, note_id: NoteID, embedding: list[float]) -> None:
    """Attach a vector directly, standing in for a completed sweep."""
    session.execute(
        note_embedding_table.insert().values(
            note_id=note_id, note_version=0, embedding=embedding, created_at=NOW
        )
    )


class TestSearchByVector:
    def test_it_returns_the_nearest_notes_first(
        self, session_factory: sessionmaker[Session]
    ):
        with session_factory() as session:
            projection = SQLAlchemyNoteProjection(session)

            far, near, exact = (note("Far"), note("Near"), note("Exact"))

            for each, embedding in (
                (far, ELSEWHERE),
                (near, NEARBY),
                (exact, HERE),
            ):
                projection.upsert(each)
                embed(session, each.id, embedding)

            found = projection.search_by_vector(OWNER, HERE, limit=10)

            assert [each.title for each in found] == ["Exact", "Near", "Far"]

    def test_the_limit_keeps_the_nearest(self, session_factory: sessionmaker[Session]):
        with session_factory() as session:
            projection = SQLAlchemyNoteProjection(session)

            for title, embedding in (("Far", ELSEWHERE), ("Exact", HERE)):
                each = note(title)
                projection.upsert(each)
                embed(session, each.id, embedding)

            found = projection.search_by_vector(OWNER, HERE, limit=1)

            assert [each.title for each in found] == ["Exact"]

    def test_a_note_without_an_embedding_cannot_be_found(
        self, session_factory: sessionmaker[Session]
    ):
        # Written seconds ago and not swept yet: absent, not ranked last.
        with session_factory() as session:
            projection = SQLAlchemyNoteProjection(session)
            projection.upsert(note("Unswept"))

            assert projection.search_by_vector(OWNER, HERE, limit=10) == []

    def test_a_deleted_note_cannot_be_found(
        self, session_factory: sessionmaker[Session]
    ):
        with session_factory() as session:
            projection = SQLAlchemyNoteProjection(session)

            gone = note("Gone", deleted=True)
            projection.upsert(gone)
            # After the upsert, which drops embeddings of its own.
            embed(session, gone.id, HERE)

            assert projection.search_by_vector(OWNER, HERE, limit=10) == []

    def test_it_never_reaches_another_users_notes(
        self, session_factory: sessionmaker[Session]
    ):
        with session_factory() as session:
            projection = SQLAlchemyNoteProjection(session)

            theirs = note("Private", owner=STRANGER)
            projection.upsert(theirs)
            embed(session, theirs.id, HERE)

            assert projection.search_by_vector(OWNER, HERE, limit=10) == []
