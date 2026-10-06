from typing import NotRequired, TypedDict

from flask import Blueprint, g, request
from flask.typing import ResponseReturnValue

from src.adapters.security.token_service import AbstractTokenService
from src.api.decorators import auth_required
from src.api.serializers import serialize_note
from src.domain.notes import Note
from src.service.uow import UOWFactory


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
        with uow_factory() as uow:
            notes = uow.notes.get_by_owner(g.user_id)

            return {"notes": [serialize_note(note) for note in notes]}

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

    return bp
