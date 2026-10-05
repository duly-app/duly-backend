from typing import Any, Sequence

from sqlalchemy import Row, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from src.adapters.orm.notes import note_table
from src.adapters.repository.notes_projection import AbstractNoteProjection
from src.domain.notes import AuthorType, Note
from src.domain.user import UserID


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

    def get_by_owner(self, owner: UserID) -> Sequence[Note]:
        rows = self._session.execute(
            select(note_table)
            .where(note_table.c.owner == owner)
            .where(note_table.c.deleted.is_(False))
            .order_by(note_table.c.last_updated.desc())
        ).all()

        return [_to_note(row) for row in rows]
