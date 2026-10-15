"""Tokens identifying a user, signed with SIGNING_KEY."""

import datetime
from enum import StrEnum

from src.adapters.security import jwt_codec
from src.adapters.security.jwt_codec import TokenPayload

ACCESS_TOKEN_LIFETIME = datetime.timedelta(minutes=15)
REFRESH_TOKEN_LIFETIME = datetime.timedelta(days=7)


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


class TokenService:
    _secret_key: str

    def __init__(self, secret_key: str):
        self._secret_key = secret_key

    def create_access_token(self, user_id: str) -> str:
        return jwt_codec.encode(
            user_id, self._secret_key, ACCESS_TOKEN_LIFETIME, TokenType.ACCESS
        )

    def create_refresh_token(self, user_id: str) -> str:
        return jwt_codec.encode(
            user_id, self._secret_key, REFRESH_TOKEN_LIFETIME, TokenType.REFRESH
        )

    def decode_token(self, token: str) -> TokenPayload[TokenType] | None:
        return jwt_codec.decode(token, self._secret_key, TokenType)

    @staticmethod
    def get_token_from_header(authorization_header: str | None) -> str | None:
        if not authorization_header:
            return None

        if not authorization_header.startswith("Bearer "):
            return None

        return authorization_header.replace("Bearer ", "", count=1)

    @property
    def secret_key(self) -> str:
        return self._secret_key
