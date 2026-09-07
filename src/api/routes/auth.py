from typing import TypedDict

from flask import Blueprint, current_app, request
from flask.typing import ResponseReturnValue

from src.adapters.security import hash_password, verify_password
from src.domain.model import Email, NewUser, Username
from src.service.uow import UOWFactory


class LoginData(TypedDict):
    email: str
    password: str


class RegistrationData(TypedDict):
    username: str
    email: str
    password: str
    registration_code: str


def create_auth_bp(uow_factory: UOWFactory) -> Blueprint:
    bp = Blueprint("auth", __name__)

    @bp.route("/login", methods=["POST"])
    def login() -> ResponseReturnValue:
        data: LoginData = request.get_json()

        email = Email(data.get("email"))
        password = data.get("password")

        unit_of_work = uow_factory()
        with unit_of_work as uow:
            user = uow.users.get_by_email(email)

            if user is None or not verify_password(user.password_hash, password):
                return {"message": "Invalid credentials"}, 401

        return {"message": "Login successful"}, 200

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
                email=email, username=username, password_hash=hash_password(password)
            )
            user_repo.create(new_user)

            uow.commit()

        return {"message": "Registration successful"}, 200

    return bp
