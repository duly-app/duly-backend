import datetime
from abc import ABC, abstractmethod
from enum import StrEnum
from typing import TypedDict


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


class TokenPayload(TypedDict):
    sub: str
    iat: datetime.datetime
    exp: datetime.datetime
    type: TokenType


class AbstractTokenService(ABC):
    _secret_key: str

    def __init__(self, secret_key: str):
        self._secret_key = secret_key

    @abstractmethod
    def create_access_token(self, user_id: str) -> str:
        pass

    @abstractmethod
    def create_refresh_token(self, user_id: str) -> str:
        pass

    @abstractmethod
    def decode_token(self, token: str) -> TokenPayload | None:
        pass

    @classmethod
    def get_token_from_header(cls, authorization_header: str | None) -> str | None:
        if not authorization_header:
            return None

        if not authorization_header.startswith("Bearer "):
            return None

        return authorization_header.replace("Bearer ", "", count=1)

    @property
    def secret_key(self) -> str:
        return self._secret_key
