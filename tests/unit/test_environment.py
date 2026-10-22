import pytest

from src.environment import EnvVar, verify_env_vars

CONFIGURED = {
    EnvVar.SIGNING_KEY: "signing-key",
    EnvVar.SERVICE_KEY: "service-key",
    EnvVar.REGISTRATION_CODE: "registration-code",
    EnvVar.DATABASE_URL: "postgresql+psycopg2://admin:password@localhost:5432/duly",
}


def test_accepts_a_complete_environment():
    verify_env_vars(CONFIGURED)


def test_rejects_a_missing_variable():
    with pytest.raises(EnvironmentError, match="SIGNING_KEY"):
        verify_env_vars({**CONFIGURED, EnvVar.SIGNING_KEY: ""})


def test_rejects_a_service_key_equal_to_the_signing_key():
    with pytest.raises(EnvironmentError):
        verify_env_vars({**CONFIGURED, EnvVar.SERVICE_KEY: "signing-key"})


def test_rejects_an_embedder_url_without_a_key():
    with pytest.raises(EnvironmentError, match="EMBEDDER_KEY"):
        verify_env_vars({**CONFIGURED, EnvVar.EMBEDDER_URL: "http://embedder-qa:8000"})


def test_accepts_an_embedder_url_with_a_key():
    verify_env_vars(
        {
            **CONFIGURED,
            EnvVar.EMBEDDER_URL: "http://embedder-qa:8000",
            EnvVar.EMBEDDER_KEY: "embedder-key",
        }
    )
