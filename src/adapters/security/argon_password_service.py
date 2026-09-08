from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from src.adapters.security.password_service import PasswordService


class ArgonPasswordService(PasswordService):
    _hasher: PasswordHasher

    def __init__(self):
        self._hasher = PasswordHasher()

    def hash_password(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify_password(self, password_hash: str, password: str) -> bool:
        try:
            return self._hasher.verify(password_hash, password)
        except VerifyMismatchError:
            return False
