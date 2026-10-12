from uuid import UUID

from tests.integration.conftest import ClientFactory
from tests.integration.fakes.helpers import auth_header

USER_ONE = UUID("00000000-0000-0000-0000-000000000001")
USER_TWO = UUID("00000000-0000-0000-0000-000000000002")
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


def test_reads_one_note_in_full(create_client: ClientFactory):
    client = create_client("test_repo")

    response = client.get(f"/api/notes/{READING_LIST}", headers=auth_header(USER_ONE))

    assert response.status_code == 200
    assert response.get_json()["title"] == "Reading list"


def test_will_not_read_another_users_note(create_client: ClientFactory):
    client = create_client("test_repo")

    response = client.get(f"/api/notes/{READING_LIST}", headers=auth_header(USER_TWO))

    # Indistinguishable from a note that does not exist.
    assert response.status_code == 404


def test_will_not_read_a_deleted_note(create_client: ClientFactory):
    client = create_client("test_repo")
    client.delete(f"/api/notes/{READING_LIST}", headers=auth_header(USER_ONE))

    response = client.get(f"/api/notes/{READING_LIST}", headers=auth_header(USER_ONE))

    assert response.status_code == 404


def test_search_passes_the_keyword_down_and_returns_the_notes_envelope(
    create_client: ClientFactory,
):
    """The route's part of searching: the query parameter and the response shape.

    Which notes match is the repository's business — here that is a fake doing
    substring matching, so asserting relevance would only describe the fake.
    """
    client = create_client("test_repo")

    response = client.get(
        "/api/notes/search?keyword=coffee", headers=auth_header(USER_ONE)
    )

    assert response.status_code == 200
    assert [note["title"] for note in response.get_json()["notes"]] == ["Shopping list"]


def test_search_needs_a_keyword(create_client: ClientFactory):
    client = create_client("test_repo")

    response = client.get("/api/notes/search", headers=auth_header(USER_ONE))

    assert response.status_code == 400


def test_search_is_scoped_to_the_caller(create_client: ClientFactory):
    """The route searches as g.user_id, never as anything from the request."""
    client = create_client("test_repo")

    response = client.get(
        "/api/notes/search?keyword=coffee", headers=auth_header(USER_TWO)
    )

    assert response.get_json()["notes"] == []


def test_search_bounds_its_page_size(create_client: ClientFactory):
    client = create_client("test_repo")

    response = client.get(
        "/api/notes/search?keyword=list&limit=1", headers=auth_header(USER_ONE)
    )

    # Both notes have "list" in the title; the limit is honoured.
    assert len(response.get_json()["notes"]) == 1
