from flask import Flask
from flask_cors import CORS

from src.api.routes import main_bp
from src.api.routes.auth import create_auth_bp
from src.api.routes.errors import internal_server_error, page_not_found
from src.bootstrap import bootstrap
from src.domain.exceptions import InvalidEmailError, InvalidUsernameError
from src.environment import verify_env_vars


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(InvalidEmailError)
    @app.errorhandler(InvalidUsernameError)
    def handle_validation_error(error: Exception):
        return {"message": str(error)}, 400

    app.register_error_handler(404, page_not_found)
    app.register_error_handler(500, internal_server_error)


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    CORS(app)

    config = config or {}
    verify_env_vars(config)
    app.config.update(config)

    register_error_handlers(app)

    deps = bootstrap(config)

    app.register_blueprint(main_bp, url_prefix="/api")
    app.register_blueprint(
        create_auth_bp(
            uow_factory=deps.uow_factory,
            password_service=deps.password_service,
            token_service=deps.token_service,
        ),
        url_prefix="/api",
    )

    return app
