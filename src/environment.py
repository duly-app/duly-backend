import os
from collections.abc import Iterable
from enum import StrEnum


class EnvVar(StrEnum):
    SECRET_KEY = "SECRET_KEY"
    REGISTRATION_CODE = "REGISTRATION_CODE"
    DATABASE_URL = "DATABASE_URL"
    TEST_DATABASE_URL = "TEST_DATABASE_URL"
    FLASK_DEBUG = "FLASK_DEBUG"


REQUIRED_ENV_VARS: tuple[EnvVar, ...] = (
    EnvVar.SECRET_KEY,
    EnvVar.REGISTRATION_CODE,
    EnvVar.DATABASE_URL,
)


def load_env_vars() -> dict[EnvVar, str]:
    return {env_var: os.environ.get(env_var.value, "") for env_var in EnvVar}


def verify_env_vars(
    env_vars: dict[EnvVar, str], required: Iterable[EnvVar] = REQUIRED_ENV_VARS
) -> None:
    missing_vars = [key.value for key in required if env_vars.get(key, "") == ""]

    if not missing_vars:
        return

    raise EnvironmentError(
        f"Missing required environment variables: {', '.join(missing_vars)}"
    )
