from argon2 import PasswordHasher as Argon2Hasher
from argon2.exceptions import VerifyMismatchError

from app.application.ports import PasswordHasher


class Argon2PasswordHasher(PasswordHasher):
    """Argon2id, OWASP's first recommendation for password storage (DEC-031)."""

    def __init__(self) -> None:
        self._hasher = Argon2Hasher()
        # Checked against when the user does not exist, so it takes the same time.
        self._dummy_hash = self._hasher.hash("dummy-password-for-timing")

    def hash(self, password: str) -> str:
        return self._hasher.hash(password)

    def verify(self, password: str, password_hash: str | None) -> bool:
        if password_hash is None:
            self._matches(self._dummy_hash, password)
            return False
        return self._matches(password_hash, password)

    def _matches(self, password_hash: str, password: str) -> bool:
        try:
            return self._hasher.verify(password_hash, password)
        except VerifyMismatchError:
            # Only a wrong password means "no match". A corrupted hash is a server
            # error and must not be reported as invalid credentials.
            return False
