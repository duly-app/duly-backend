import json
from datetime import datetime
from pathlib import Path
from uuid import UUID

from src.domain.model import Email, User, Username
from src.domain.roles import Role

CURRENT_FILE = Path(__file__)
USER_REPOS = CURRENT_FILE.parent / "user_repos"


assert USER_REPOS.exists(), f"Directory {USER_REPOS!s} does not exist"


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


def get_users(repo_name: str) -> list[User]:
    repo_path = USER_REPOS / repo_name

    return parse_users_json(repo_path / "users.json")
