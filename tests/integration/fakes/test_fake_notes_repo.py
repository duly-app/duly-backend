from uuid import UUID

from src.domain.notes import AuthorType, Note
from tests.integration.conftest import DBFactory, NotesRepoFactory

USER_ONE = UUID("00000000-0000-0000-0000-000000000001")
USER_TWO = UUID("00000000-0000-0000-0000-000000000002")

SHOPPING_LIST = UUID("70000000-0000-0000-0000-000000000001")
READING_LIST = UUID("70000000-0000-0000-0000-000000000002")
DELETED_NOTE = UUID("70000000-0000-0000-0000-000000000004")


def test_replays_a_single_event_stream(create_notes_repo: NotesRepoFactory):
    repo = create_notes_repo("test_repo")
    note = repo.get_by_id(SHOPPING_LIST)

    assert note is not None
    assert note.title == "Shopping list"
    assert note.version == 1


def test_replays_an_updated_stream(create_notes_repo: NotesRepoFactory):
    repo = create_notes_repo("test_repo")
    note = repo.get_by_id(READING_LIST)

    assert note is not None
    assert "Architecture Patterns with Python" in note.content
    assert note.version == 2
    assert note.last_author_type == AuthorType.AI


def test_unknown_note_is_none(create_notes_repo: NotesRepoFactory):
    repo = create_notes_repo("test_repo")

    assert repo.get_by_id(UUID("70000000-0000-0000-0000-00000000dead")) is None


def test_projection_is_seeded_from_the_event_log(create_notes_repo: NotesRepoFactory):
    repo = create_notes_repo("test_repo")
    titles = [note.title for note in repo.get_by_owner(USER_ONE)]

    assert titles == ["Reading list", "Shopping list"]


def test_projection_excludes_deleted_notes(create_notes_repo: NotesRepoFactory):
    repo = create_notes_repo("test_repo")
    notes = repo.get_by_owner(USER_TWO)

    assert [note.title for note in notes] == ["Gym plan"]

    assert repo.get_by_id(DELETED_NOTE) is None


def test_saving_a_note_appends_events_and_projects_it(
    create_notes_repo: NotesRepoFactory,
):
    repo = create_notes_repo("test_repo")
    note = Note.create(title="Fresh", content="Brand new", owner=USER_ONE)

    repo.save(note)

    assert repo.get_by_id(note.id) is not None
    assert "Fresh" in [n.title for n in repo.get_by_owner(USER_ONE)]
    assert note.events == []


def test_updating_a_note_is_reflected_in_the_projection(
    create_notes_repo: NotesRepoFactory,
):
    repo = create_notes_repo("test_repo")
    note = repo.get_by_id(READING_LIST)
    assert note is not None

    note.update(title="Reading list 2026", content="Still reading", author_id=USER_ONE)
    repo.save(note)

    projected = next(n for n in repo.get_by_owner(USER_ONE) if n.id == READING_LIST)
    assert projected.title == "Reading list 2026"
    assert projected.version == 3


def test_deleting_a_note_removes_it_from_the_projection(
    create_notes_repo: NotesRepoFactory,
):
    repo = create_notes_repo("test_repo")
    note = repo.get_by_id(SHOPPING_LIST)
    assert note is not None

    repo.delete(note, USER_ONE)

    assert [n.title for n in repo.get_by_owner(USER_ONE)] == ["Reading list"]
    assert repo.get_by_id(SHOPPING_LIST) is None


def test_deleting_a_note_keeps_its_history(create_notes_repo: NotesRepoFactory):
    repo = create_notes_repo("test_repo")
    note = repo.get_by_id(SHOPPING_LIST)
    assert note is not None

    repo.delete(note, USER_ONE)

    events = repo._event_store.get_events(SHOPPING_LIST)
    assert [type(event).__name__ for event in events] == [
        "NoteCreatedEvent",
        "NoteDeletedEvent",
    ]


def test_notes_of_other_owners_are_not_returned(create_notes_repo: NotesRepoFactory):
    repo = create_notes_repo("test_repo")

    assert all(note.owner == USER_ONE for note in repo.get_by_owner(USER_ONE))


def test_create_db_gives_both_repositories(create_db: DBFactory):
    db = create_db("test_repo")

    assert len(db.users.get(0, 100)) == 2
    assert len(db.notes.get_by_owner(USER_ONE)) == 2
