from functools import wraps
from typing import Callable, ParamSpec

from flask import g, request
from flask.typing import ResponseReturnValue

from src.adapters.security.token_service import AbstractTokenService, TokenType
from src.domain.user import UserID

P = ParamSpec("P")

View = Callable[P, ResponseReturnValue]


def authenticated_user_id(token_service: AbstractTokenService) -> UserID | None:
    """Resolve the caller from a Bearer access token, or None if it is not usable."""
    token = token_service.get_token_from_header(request.headers.get("Authorization"))
    if not token:
        return None

    payload = token_service.decode_token(token)
    if payload is None:
        return None

    if payload["type"] is not TokenType.ACCESS:
        return None

    return UserID(payload["sub"])


def auth_required(
    token_service: AbstractTokenService,
) -> Callable[[View[P]], View[P]]:
    """Build a decorator that rejects unauthenticated requests and sets g.user_id."""

    def decorator(view: View[P]) -> View[P]:
        @wraps(view)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> ResponseReturnValue:
            user_id = authenticated_user_id(token_service)

            if user_id is None:
                return {"message": "Unauthorized"}, 401

            g.user_id = user_id

            return view(*args, **kwargs)

        return wrapper

    return decorator
