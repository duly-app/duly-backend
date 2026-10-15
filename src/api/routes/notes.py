from datetime import datetime
from typing import Literal, NotRequired, TypedDict
from uuid import UUID

from flask import Blueprint, g, request
from flask.typing import ResponseReturnValue

from src.adapters.repository import NoteOrder
from src.adapters.security.token_service import AbstractTokenService
from src.api.decorators import auth_required
from src.api.serializers import serialize_note
from src.domain.notes import Note
from src.service.uow import UOWFactory

DEFAULT_SEARCH_LIMIT = 20
MAX_SEARCH_LIMIT = 50


def _order() -> tuple[NoteOrder, bool]:
    try:
        order_by = NoteOrder(request.args.get("order_by", NoteOrder.LAST_UPDATED.value))
    except ValueError:
        order_by = NoteOrder.LAST_UPDATED

    return order_by, request.args.get("direction", "desc").lower() != "asc"


def _updated(name: Literal["updated_after", "updated_before"]) -> datetime | None:
    value = request.args.get(name)

    if not value:
        return None

    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _limit() -> int:
    """Bound the caller's page size, so one request cannot ask for everything."""
    try:
        requested = int(request.args.get("limit", DEFAULT_SEARCH_LIMIT))
    except ValueError:
        return DEFAULT_SEARCH_LIMIT

    return max(1, min(requested, MAX_SEARCH_LIMIT))


class NotesData(TypedDict):
    # Both keys may be absent by the caller.
    title: NotRequired[str]
    content: NotRequired[str]


def create_notes_bp(
    uow_factory: UOWFactory,
    token_service: AbstractTokenService,
) -> Blueprint:
    bp = Blueprint("notes", __name__)
    require_auth = auth_required(token_service)

    @bp.route("/notes", methods=["GET"])
    @require_auth
    def get_notes() -> ResponseReturnValue:
        order_by, descending = _order()

        with uow_factory() as uow:
            notes = uow.notes.get_by_owner(
                g.user_id,
                order_by=order_by,
                descending=descending,
                updated_after=_updated("updated_after"),
                updated_before=_updated("updated_before"),
            )

            return {"notes": [serialize_note(note) for note in notes]}

    @bp.route("/notes/search", methods=["GET"])
    @require_auth
    def search_notes() -> ResponseReturnValue:
        keyword = request.args.get("keyword", "").strip()

        if not keyword:
            return {"message": "A keyword is required"}, 400

        notes = []

        with uow_factory() as uow:
            notes = list(uow.notes.search(g.user_id, keyword, _limit()))

        return {"notes": [serialize_note(note) for note in notes]}

    @bp.route("/notes/<uuid:note_id>", methods=["GET"])
    @require_auth
    def get_note(note_id: UUID) -> ResponseReturnValue:
        with uow_factory() as uow:
            note = uow.notes.get_by_id(note_id)

            if note is None or note.owner != g.user_id:
                return {"message": "Note not found"}, 404

            return serialize_note(note)

    @bp.route("/notes", methods=["POST"])
    @require_auth
    def add_note() -> ResponseReturnValue:
        data: NotesData | None = request.get_json(silent=True)

        if data is None:
            return {"message": "A JSON body is required"}, 400

        title = data.get("title", "").strip()
        content = data.get("content", "")

        if not title:
            return {"message": "A title is required"}, 400

        note = Note.create(title=title, content=content, owner=g.user_id)

        with uow_factory() as uow:
            uow.notes.save(note)
            uow.commit()

        return serialize_note(note), 201

    @bp.route("/notes/<uuid:note_id>", methods=["PUT"])
    @require_auth
    def update_note(note_id: UUID) -> ResponseReturnValue:
        data: NotesData | None = request.get_json(silent=True)

        if data is None:
            return {"message": "A JSON body is required"}, 400

        title = data.get("title")
        content = data.get("content")

        if title is None and content is None:
            return {"message": "A title or content is required"}, 400

        with uow_factory() as uow:
            note = uow.notes.get_by_id(note_id)

            if note is None or note.owner != g.user_id:
                return {"message": "Note not found"}, 404

            new_title = (note.title if title is None else title).strip()

            if not new_title:
                return {"message": "A title is required"}, 400

            note.update(
                title=new_title,
                content=note.content if content is None else content,
                author_id=g.user_id,
            )

            uow.notes.save(note)
            uow.commit()

            return serialize_note(note)

    @bp.route("/notes/<uuid:note_id>", methods=["DELETE"])
    @require_auth
    def delete_note(note_id: UUID) -> ResponseReturnValue:
        with uow_factory() as uow:
            note = uow.notes.get_by_id(note_id)

            if note is None or note.owner != g.user_id:
                return {"message": "Note not found"}, 404

            uow.notes.delete(note, g.user_id)
            uow.commit()

        return "", 204

    return bp
