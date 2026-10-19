import os
from collections.abc import Iterable
from enum import StrEnum


class EnvVar(StrEnum):
    SIGNING_KEY = "SIGNING_KEY"
    SERVICE_KEY = "SERVICE_KEY"
    REGISTRATION_CODE = "REGISTRATION_CODE"
    DATABASE_URL = "DATABASE_URL"
    TEST_DATABASE_URL = "TEST_DATABASE_URL"
    FLASK_DEBUG = "FLASK_DEBUG"
    LOG_LEVEL = "LOG_LEVEL"
    EMBEDDER_URL = "EMBEDDER_URL"
    EMBEDDER_KEY = "EMBEDDER_KEY"
    # Set by Werkzeug in the reloader's child process, not by us
    # Kept for dependency injection
    WERKZEUG_RUN_MAIN = "WERKZEUG_RUN_MAIN"


REQUIRED_ENV_VARS: tuple[EnvVar, ...] = (
    EnvVar.SIGNING_KEY,
    EnvVar.SERVICE_KEY,
    EnvVar.REGISTRATION_CODE,
    EnvVar.DATABASE_URL,
)


def load_env_vars() -> dict[EnvVar, str]:
    return {env_var: os.environ.get(env_var.value, "") for env_var in EnvVar}


def verify_env_vars(
    env_vars: dict[EnvVar, str], required: Iterable[EnvVar] = REQUIRED_ENV_VARS
) -> None:
    missing_vars = [key.value for key in required if env_vars.get(key, "") == ""]

    if missing_vars:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )

    signing_key = env_vars.get(EnvVar.SIGNING_KEY)

    if signing_key and signing_key == env_vars.get(EnvVar.SERVICE_KEY):
        raise EnvironmentError("SERVICE_KEY must differ from SIGNING_KEY for security.")
