import json
from datetime import datetime
from pathlib import Path
from uuid import UUID

from src.adapters.repository.sqlalchemy_notes_event_store import event_from_dict
from src.domain.notes import NoteEvent
from src.domain.roles import Role
from src.domain.user import Email, User, Username

CURRENT_FILE = Path(__file__)
DATABASES = CURRENT_FILE.parent / "databases"


assert DATABASES.exists(), f"Directory {DATABASES!s} does not exist"


def parse_users_json(json_path: Path) -> list[User]:
    with open(json_path) as f:
        records = json.load(f)

    return [
        User(
            id=UUID(r["id"]),
            username=Username(r["username"]),
            email=Email(r["email"]),
            password_hash=r["password_hash"],
            created_at=datetime.fromisoformat(r["created_at"]),
            verified=r.get("verified", False),
            role=Role[r.get("role", "USER")],
        )
        for r in records
    ]


def parse_note_events_json(json_path: Path) -> list[NoteEvent]:
    with open(json_path) as f:
        records = json.load(f)

    return [
        event_from_dict(
            {
                **r,
                "id": UUID(r["id"]),
                "note_id": UUID(r["note_id"]),
                "author_id": UUID(r["author_id"]),
                "timestamp": datetime.fromisoformat(r["timestamp"]),
            }
        )
        for r in records
    ]


def get_users(db_name: str) -> list[User]:
    return parse_users_json(DATABASES / db_name / "users.json")


def get_note_events(db_name: str) -> list[NoteEvent]:
    return parse_note_events_json(DATABASES / db_name / "note_events.json")


def parse_db(db_name: str) -> tuple[list[User], list[NoteEvent]]:
    return get_users(db_name), get_note_events(db_name)
