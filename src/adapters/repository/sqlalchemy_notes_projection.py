from datetime import datetime
from typing import Any, Sequence

from sqlalchemy import Row, delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.adapters.orm.notes import note_embedding_table, note_table
from src.adapters.repository.notes_projection import AbstractNoteProjection, NoteOrder
from src.domain.notes import AuthorType, Note
from src.domain.user import UserID

_ORDER_COLUMNS = {
    NoteOrder.LAST_UPDATED: note_table.c.last_updated,
    NoteOrder.CREATED_AT: note_table.c.created_at,
    NoteOrder.TITLE: note_table.c.title,
}


def _to_values(note: Note) -> dict[str, Any]:
    return {
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "created_at": note.created_at,
        "last_updated": note.last_updated,
        "updated_by": note.updated_by,
        "last_author_type": note.last_author_type.value,
        "owner": note.owner,
        "deleted": note.deleted,
        "version": note.version,
    }


def _to_note(row: Row[Any]) -> Note:
    return Note(
        id=row.id,
        title=row.title,
        content=row.content,
        created_at=row.created_at,
        last_updated=row.last_updated,
        updated_by=row.updated_by,
        last_author_type=AuthorType(row.last_author_type),
        owner=row.owner,
        deleted=row.deleted,
        version=row.version,
    )


class SQLAlchemyNoteProjection(AbstractNoteProjection):
    _session: Session

    def __init__(self, session: Session):
        self._session = session

    def upsert(self, note: Note) -> None:
        values = _to_values(note)

        statement = insert(note_table).values(**values)
        statement = statement.on_conflict_do_update(
            index_elements=[note_table.c.id],
            set_={key: value for key, value in values.items() if key != "id"},
        )

        self._session.execute(statement)

        # Whatever embedding exists describes the text this write replaces, so
        # it is now wrong. Dropping the row is how the sweeper is told to recompute
        self._session.execute(
            delete(note_embedding_table).where(
                note_embedding_table.c.note_id == note.id
            )
        )

    def search(self, owner: UserID, query: str, limit: int) -> Sequence[Note]:
        # websearch_to_tsquery, not to_tsquery: this one
        # accepts anything a person or a model would type, quotes and all.
        tsquery = func.websearch_to_tsquery("english", query)

        rows = self._session.execute(
            select(note_table)
            .where(note_table.c.owner == owner)
            .where(note_table.c.deleted.is_(False))
            .where(note_table.c.search_vector.op("@@")(tsquery))
            # Ranked, because the caller takes the first N: without an order
            # the best match can fall outside the limit and never be seen.
            .order_by(func.ts_rank(note_table.c.search_vector, tsquery).desc())
            .limit(limit)
        ).all()

        return [_to_note(row) for row in rows]

    def search_by_vector(
        self, owner: UserID, embedding: Sequence[float], limit: int
    ) -> Sequence[Note]:
        distance = note_embedding_table.c.embedding.cosine_distance(list(embedding))

        rows = self._session.execute(
            select(note_table)
            .join(
                note_embedding_table,
                note_embedding_table.c.note_id == note_table.c.id,
            )
            .where(note_table.c.owner == owner)
            .where(note_table.c.deleted.is_(False))
            .order_by(distance)
            .limit(limit)
        ).all()

        return [_to_note(row) for row in rows]

    def get_by_owner(
        self,
        owner: UserID,
        order_by: NoteOrder = NoteOrder.LAST_UPDATED,
        descending: bool = True,
        updated_after: datetime | None = None,
        updated_before: datetime | None = None,
    ) -> Sequence[Note]:
        column = _ORDER_COLUMNS[order_by]

        statement = (
            select(note_table)
            .where(note_table.c.owner == owner)
            .where(note_table.c.deleted.is_(False))
        )

        if updated_after is not None:
            statement = statement.where(note_table.c.last_updated >= updated_after)

        if updated_before is not None:
            statement = statement.where(note_table.c.last_updated < updated_before)

        return [
            _to_note(row)
            for row in self._session.execute(
                statement.order_by(
                    column.desc() if descending else column.asc(),
                    note_table.c.id,
                )
            ).all()
        ]
