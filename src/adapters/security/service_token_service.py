"""The credential proving a write came from the assistant rather than a person."""

from enum import StrEnum

from src.adapters.security import jwt_codec

SERVICE_TOKEN_HEADER = "X-Service-Token"
SERVICE_SUBJECT = "duly-chat-backend"


class ServiceTokenType(StrEnum):
    SERVICE = "service"


class ServiceTokenService:
    _secret_key: str

    def __init__(self, secret_key: str):
        self._secret_key = secret_key

    def is_trusted_service(self, token: str | None) -> bool:
        """Whether this token was minted by a service allowed to author notes."""
        if not token:
            return False

        payload = jwt_codec.decode(token, self._secret_key, ServiceTokenType)

        if payload is None:
            return False

        return payload["sub"] == SERVICE_SUBJECT
