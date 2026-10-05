class NoteAlreadyExistsError(Exception):
    """Raised when a note with the same title already exists for the user."""


class NoteAlreadyDeletedError(Exception):
    """Raised when a note is already deleted and cannot be modified."""


class NoteIdMismatchError(Exception):
    """Raised when a note event's note_id does not match the note's id."""


class NoteTimestampError(Exception):
    """Raised when a note event's timestamp is earlier than the note's last_updated \
timestamp."""


class NoUpdateDeletedNoteError(Exception):
    """Raised when trying to update a deleted note."""
