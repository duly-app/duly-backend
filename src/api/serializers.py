from typing import Any

from src.domain.notes import Note


def serialize_note(note: Note) -> dict[str, Any]:
    """Shape a note for the API.

    Deliberately narrower than the aggregate
    """
    return {
        "id": str(note.id),
        "title": note.title,
        "content": note.content,
        "created_at": note.created_at.isoformat(),
        "last_updated": note.last_updated.isoformat(),
        "last_author_type": note.last_author_type.value,
    }
