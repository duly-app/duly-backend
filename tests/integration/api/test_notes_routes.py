from uuid import UUID

from tests.integration.conftest import ClientFactory
from tests.integration.fakes.helpers import auth_header

USER_ONE = UUID("00000000-0000-0000-0000-000000000001")
READING_LIST = UUID("70000000-0000-0000-0000-000000000002")


def test_lists_the_users_notes(create_client: ClientFactory):
    client = create_client("test_repo")

    response = client.get("/api/notes", headers=auth_header(USER_ONE))

    assert response.status_code == 200
    assert [note["title"] for note in response.get_json()["notes"]] == [
        "Reading list",
        "Shopping list",
    ]


def test_creates_a_note_and_lists_it(create_client: ClientFactory):
    client = create_client("test_repo")

    response = client.post(
        "/api/notes",
        json={"title": "Fresh", "content": "Brand new"},
        headers=auth_header(USER_ONE),
    )

    assert response.status_code == 201
    assert response.get_json()["title"] == "Fresh"

    listed = client.get("/api/notes", headers=auth_header(USER_ONE)).get_json()
    assert "Fresh" in [note["title"] for note in listed["notes"]]


def test_updates_a_note(create_client: ClientFactory):
    client = create_client("test_repo")

    response = client.put(
        f"/api/notes/{READING_LIST}",
        json={"title": "Reading list 2026"},
        headers=auth_header(USER_ONE),
    )

    assert response.status_code == 200
    assert response.get_json()["title"] == "Reading list 2026"
    # Content was not sent, so it keeps its current value.
    assert "Architecture Patterns with Python" in response.get_json()["content"]


def test_deletes_a_note(create_client: ClientFactory):
    client = create_client("test_repo")

    response = client.delete(
        f"/api/notes/{READING_LIST}", headers=auth_header(USER_ONE)
    )

    assert response.status_code == 204

    listed = client.get("/api/notes", headers=auth_header(USER_ONE)).get_json()
    assert [note["title"] for note in listed["notes"]] == ["Shopping list"]


def test_rejects_an_unauthenticated_request(create_client: ClientFactory):
    client = create_client("test_repo")

    assert client.get("/api/notes").status_code == 401
