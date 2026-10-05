from typing import TypedDict

from flask import Blueprint, Response, current_app, jsonify, request
from flask.typing import ResponseReturnValue

from src.adapters.security.jwt_token_service import REFRESH_TOKEN_LIFETIME
from src.adapters.security.password_service import PasswordService
from src.adapters.security.token_service import AbstractTokenService, TokenType
from src.domain.user import Email, NewUser, UserID, Username
from src.service.uow import UOWFactory

REFRESH_COOKIE = "refresh_token"

REFRESH_COOKIE_PATH = "/api/refresh"


class LoginData(TypedDict):
    email: str
    password: str


class RegistrationData(TypedDict):
    username: str
    email: str
    password: str
    registration_code: str


def start_session(
    token_service: AbstractTokenService, user_id: str, message: str
) -> Response:
    """Hand back an access token in the body and a refresh token in a cookie."""
    access_token = token_service.create_access_token(user_id)
    response = jsonify({"message": message, "token": access_token})

    response.set_cookie(
        REFRESH_COOKIE,
        token_service.create_refresh_token(user_id),
        max_age=int(REFRESH_TOKEN_LIFETIME.total_seconds()),
        httponly=True,
        # Browsers reject Secure cookies over plain http, so localhost needs it off.
        secure=current_app.config.get("FLASK_DEBUG") != "1",
        samesite="Lax",
        path=REFRESH_COOKIE_PATH,
    )

    return response


def create_auth_bp(
    uow_factory: UOWFactory,
    password_service: PasswordService,
    token_service: AbstractTokenService,
) -> Blueprint:
    bp = Blueprint("auth", __name__)

    @bp.route("/login", methods=["POST"])
    def login() -> ResponseReturnValue:
        data: LoginData = request.get_json()

        email = Email(data.get("email"))
        password = data.get("password")

        unit_of_work = uow_factory()
        with unit_of_work as uow:
            user = uow.users.get_by_email(email)

            if user is None or not password_service.verify_password(
                user.password_hash, password
            ):
                return {"message": "Invalid credentials"}, 401

            user_id = str(user.id)

        return start_session(token_service, user_id, "Login successful")

    @bp.route("/signup", methods=["POST"])
    def signup() -> ResponseReturnValue:
        data: RegistrationData = request.get_json()

        email = Email(data.get("email"))
        username = Username(data.get("username"))
        registration_code = data.get("registration_code")
        password = data.get("password")

        if registration_code != current_app.config["REGISTRATION_CODE"]:
            return {"message": "Invalid registration code"}, 403

        unit_of_work = uow_factory()

        with unit_of_work as uow:
            user_repo = uow.users
            email_in_use = user_repo.get_by_email(email) is not None

            if email_in_use:
                return {"message": "Email already exists"}, 409

            username_in_use = user_repo.get_by_username(username) is not None
            if username_in_use:
                return {"message": "Username already exists"}, 409

            new_user = NewUser(
                email=email,
                username=username,
                password_hash=password_service.hash_password(password),
            )
            user_repo.create(new_user)

            uow.commit()

        return {"message": "Registration successful"}, 200

    @bp.route("/refresh", methods=["POST"])
    def refresh() -> ResponseReturnValue:
        token = request.cookies.get(REFRESH_COOKIE)
        if not token:
            return {"message": "Unauthorized"}, 401

        token_payload = token_service.decode_token(token)
        if token_payload is None:
            return {"message": "Unauthorized"}, 401

        if token_payload["type"] is not TokenType.REFRESH:
            return {"message": "Unauthorized"}, 401

        return start_session(
            token_service, str(token_payload["sub"]), "Token refreshed"
        )

    @bp.route("/logout", methods=["POST"])
    def logout() -> ResponseReturnValue:
        response = jsonify({"message": "Logged out"})
        response.delete_cookie(REFRESH_COOKIE, path=REFRESH_COOKIE_PATH)

        return response

    @bp.route("/me", methods=["GET"])
    def me() -> ResponseReturnValue:
        token = token_service.get_token_from_header(
            request.headers.get("Authorization")
        )
        if not token:
            return {"message": "Unauthorized"}, 401

        token_payload = token_service.decode_token(token)
        if token_payload is None:
            return {"message": "Unauthorized"}, 401

        if token_payload["type"] is not TokenType.ACCESS:
            return {"message": "Unauthorized"}, 401

        with uow_factory() as uow:
            user = uow.users.get_by_id(UserID(token_payload["sub"]))
            if not user:
                return {"message": "Unauthorized"}, 401

            return {
                "id": str(user.id),
                "email": str(user.email),
                "username": str(user.username),
            }, 200

    return bp
