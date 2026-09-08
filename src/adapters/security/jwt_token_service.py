import datetime

import jwt

from src.adapters.security.token_service import AbstractTokenService, TokenPayload


class JWTTokenService(AbstractTokenService):
    def create_access_token(self, user_id: str) -> str:
        return self.create_token(
            user_id, self._secret_key, datetime.timedelta(minutes=15)
        )

    def create_refresh_token(self, user_id: str) -> str:
        return self.create_token(user_id, self._secret_key, datetime.timedelta(days=7))

    def decode_token(self, token: str) -> TokenPayload | None:
        try:
            decoding = jwt.decode(token, self._secret_key, algorithms=["HS256"])

            return {
                "sub": decoding["sub"],
                "iat": decoding["iat"],
                "exp": decoding["exp"],
            }
        except jwt.PyJWTError:
            return None

    @classmethod
    def create_token(
        cls, user_id: str, secret_key: str, expires_delta: datetime.timedelta
    ) -> str:
        now = datetime.datetime.now(datetime.timezone.utc)

        payload = {"sub": user_id, "iat": now, "exp": now + expires_delta}

        return jwt.encode(payload, secret_key, algorithm="HS256")
