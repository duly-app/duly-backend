from dataclasses import dataclass

from pgvector.sqlalchemy import Vector
from sqlalchemy import func, literal, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.adapters.embedding import Embedding
from src.adapters.orm.notes import (
    EMBEDDING_DIMENSIONS,
    note_embedding_table,
    note_table,
)
from src.domain.notes import NoteID


@dataclass(frozen=True)
class PendingNote:
    """A note waiting to be embedded, with the version it was read at."""

    id: NoteID
    version: int
    title: str
    content: str

    @property
    def text(self) -> str:
        return f"{self.title}\n\n{self.content}"


def fetch_pending_notes(session: Session, limit: int) -> list[PendingNote]:
    rows = session.execute(
        select(
            note_table.c.id,
            note_table.c.version,
            note_table.c.title,
            note_table.c.content,
        )
        .outerjoin(
            note_embedding_table,
            note_embedding_table.c.note_id == note_table.c.id,
        )
        .where(note_embedding_table.c.note_id.is_(None))
        .where(note_table.c.deleted.is_(False))
        .order_by(note_table.c.last_updated)
        .limit(limit)
    ).all()

    return [
        PendingNote(
            id=row.id, version=row.version, title=row.title, content=row.content
        )
        for row in rows
    ]


def store_embedding(
    session: Session, note_id: NoteID, note_version: int, embedding: Embedding
) -> bool:
    """Save an embedding, unless the note has moved on since it was read.

    Returns whether the row was written.
    """
    source = select(
        note_table.c.id,
        note_table.c.version,
        literal(embedding, Vector(EMBEDDING_DIMENSIONS)),
        func.now(),
    ).where(
        note_table.c.id == note_id,
        note_table.c.version == note_version,
        note_table.c.deleted.is_(False),
    )

    statement = insert(note_embedding_table).from_select(
        ["note_id", "note_version", "embedding", "created_at"], source
    )
    upsert = statement.on_conflict_do_update(
        index_elements=[note_embedding_table.c.note_id],
        set_={
            "note_version": statement.excluded.note_version,
            "embedding": statement.excluded.embedding,
            "created_at": statement.excluded.created_at,
        },
    ).returning(note_embedding_table.c.note_id)

    return session.execute(upsert).scalar_one_or_none() is not None
