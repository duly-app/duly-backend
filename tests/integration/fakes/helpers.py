import json
from datetime import datetime, timedelta
from pathlib import Path
from uuid import UUID

from src.adapters.repository.sqlalchemy_notes_event_store import event_from_dict
from src.adapters.security import jwt_codec
from src.adapters.security.service_token_service import (
    SERVICE_SUBJECT,
    SERVICE_TOKEN_HEADER,
    ServiceTokenType,
)
from src.adapters.security.token_service import TokenService
from src.domain.notes import NoteEvent
from src.domain.roles import Role
from src.domain.user import Email, User, UserID, Username

CURRENT_FILE = Path(__file__)
DATABASES = CURRENT_FILE.parent / "databases"

TEST_SECRET_KEY = "test-secret-key-at-least-32-characters"
TEST_SERVICE_KEY = "test-service-key-at-least-32-characters"


assert DATABASES.exists(), f"Directory {DATABASES!s} does not exist"


def auth_header(user_id: UserID) -> dict[str, str]:
    token = TokenService(TEST_SECRET_KEY).create_access_token(str(user_id))

    return {"Authorization": f"Bearer {token}"}


def service_header(
    secret_key: str = TEST_SERVICE_KEY,
    subject: str = SERVICE_SUBJECT,
    lifetime: timedelta = timedelta(seconds=60),
) -> dict[str, str]:
    """The header duly-chat-backend sends on a write, as the assistant."""
    token = jwt_codec.encode(subject, secret_key, lifetime, ServiceTokenType.SERVICE)

    return {SERVICE_TOKEN_HEADER: token}


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
