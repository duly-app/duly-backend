from flask import Blueprint, request

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    user_agent = request.headers.get("User-Agent")
    return f"Hello, {user_agent}!"
