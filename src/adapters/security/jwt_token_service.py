import datetime

import jwt

from src.adapters.security.token_service import (
    AbstractTokenService,
    TokenPayload,
    TokenType,
)

ACCESS_TOKEN_LIFETIME = datetime.timedelta(minutes=15)
REFRESH_TOKEN_LIFETIME = datetime.timedelta(days=7)


class JWTTokenService(AbstractTokenService):
    def create_access_token(self, user_id: str) -> str:
        return self.create_token(
            user_id, self._secret_key, ACCESS_TOKEN_LIFETIME, TokenType.ACCESS
        )

    def create_refresh_token(self, user_id: str) -> str:
        return self.create_token(
            user_id, self._secret_key, REFRESH_TOKEN_LIFETIME, TokenType.REFRESH
        )

    def decode_token(self, token: str) -> TokenPayload | None:
        try:
            decoding = jwt.decode(token, self._secret_key, algorithms=["HS256"])

            return {
                "sub": decoding["sub"],
                "iat": decoding["iat"],
                "exp": decoding["exp"],
                "type": TokenType(decoding.get("type", TokenType.ACCESS)),
            }
        except (jwt.PyJWTError, ValueError):
            return None

    @classmethod
    def create_token(
        cls,
        user_id: str,
        secret_key: str,
        expires_delta: datetime.timedelta,
        token_type: TokenType = TokenType.ACCESS,
    ) -> str:
        now = datetime.datetime.now(datetime.timezone.utc)

        payload = {
            "sub": user_id,
            "iat": now,
            "exp": now + expires_delta,
            "type": token_type.value,
        }

        return jwt.encode(payload, secret_key, algorithm="HS256")
