from typing import TypedDict

from flask import Blueprint, current_app, request
from flask.typing import ResponseReturnValue

from src.adapters.security.password_service import PasswordService
from src.adapters.security.token_service import AbstractTokenService
from src.domain.model import Email, NewUser, UserID, Username
from src.service.uow import UOWFactory


class LoginData(TypedDict):
    email: str
    password: str


class RegistrationData(TypedDict):
    username: str
    email: str
    password: str
    registration_code: str


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

            access_token = token_service.create_access_token(str(user.id))

        return {"message": "Login successful", "token": access_token}, 200

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
                return {"message": "Email already exists"}, 400

            username_in_use = user_repo.get_by_username(username) is not None
            if username_in_use:
                return {"message": "Username already exists"}, 400

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
        token = request.headers.get("Authorization")
        if not token:
            return {"message": "Unauthorized"}, 401

        token_payload = token_service.decode_token(token)
        if token_payload is None:
            return {"message": "Unauthorized"}, 401

        access_token = token_service.create_access_token(str(token_payload["sub"]))

        return {"message": "Token refreshed", "token": access_token}, 200

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

        with uow_factory() as uow:
            user = uow.users.get_by_id(UserID(token_payload["sub"]))
            if not user:
                return {"message": "User not found"}, 404

            return {
                "id": str(user.id),
                "email": str(user.email),
                "username": str(user.username),
            }, 200

    return bp
