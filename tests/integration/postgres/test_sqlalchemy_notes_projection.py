from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from src.adapters.orm.notes import EMBEDDING_DIMENSIONS, note_embedding_table
from src.adapters.repository.sqlalchemy_notes_projection import (
    SQLAlchemyNoteProjection,
)
from src.domain.notes import AuthorType, Note

OWNER = UUID("550e8400-e29b-41d4-a716-446655440099")
NOTE_ID = UUID("9f1c7a52-3b6e-4f80-9d21-7a4e5c8b2001")
BLOB = [0.1] * EMBEDDING_DIMENSIONS


def note(title: str, content: str, version: int) -> Note:
    now = datetime(2026, 10, 18, 12, 0, tzinfo=timezone.utc)

    return Note(
        id=NOTE_ID,
        title=title,
        content=content,
        created_at=now,
        last_updated=now,
        updated_by=OWNER,
        last_author_type=AuthorType.USER,
        owner=OWNER,
        version=version,
    )


class TestSQLAlchemyNoteProjection:
    def test_writing_a_note_discards_the_embedding_of_the_old_text(
        self, session_factory: sessionmaker[Session]
    ):
        with session_factory() as session:
            projection = SQLAlchemyNoteProjection(session)

            projection.upsert(note("Sourdough", "Fed the starter.", version=0))
            session.execute(
                note_embedding_table.insert().values(
                    note_id=NOTE_ID,
                    note_version=0,
                    embedding=BLOB,
                    created_at=datetime.now(timezone.utc),
                )
            )

            assert self._embedded_versions(session) == [0]

            projection.upsert(note("Sourdough", "Fed the rye starter.", version=1))

            assert self._embedded_versions(session) == []

    def test_writing_a_note_that_was_never_embedded_is_fine(
        self, session_factory: sessionmaker[Session]
    ):
        with session_factory() as session:
            projection = SQLAlchemyNoteProjection(session)

            projection.upsert(note("Pasta", "100g flour to one egg.", version=0))

            assert self._embedded_versions(session) == []

    @staticmethod
    def _embedded_versions(session: Session) -> list[int]:
        return list(
            session.scalars(
                select(note_embedding_table.c.note_version).where(
                    note_embedding_table.c.note_id == NOTE_ID
                )
            ).all()
        )
