from datetime import datetime, timedelta
from uuid import UUID

import jwt

from app.application.dto import IssuedToken
from app.application.ports import TokenService
from app.domain.exceptions import InvalidToken

_ALGORITHM = "HS256"


class JwtTokenService(TokenService):
    """HS256 JWT access tokens carrying only ``sub``, ``iat`` and ``exp`` (DEC-030)."""

    def __init__(self, *, secret_key: str, expire_minutes: int) -> None:
        self._secret_key = secret_key
        self._lifetime = timedelta(minutes=expire_minutes)

    def issue(self, user_id: UUID, *, now: datetime) -> IssuedToken:
        payload = {
            "sub": str(user_id),
            "iat": int(now.timestamp()),
            "exp": int((now + self._lifetime).timestamp()),
        }
        token = jwt.encode(payload, self._secret_key, algorithm=_ALGORITHM)
        return IssuedToken(
            access_token=token, expires_in=int(self._lifetime.total_seconds())
        )

    def decode(self, token: str, *, now: datetime) -> UUID:
        try:
            # Time-based claims are checked below against the injected clock instead
            # of PyJWT's internal one, so tests stay deterministic (DEC-038).
            payload = jwt.decode(
                token,
                self._secret_key,
                algorithms=[_ALGORITHM],
                options={
                    "require": ["sub", "iat", "exp"],
                    "verify_exp": False,
                    "verify_iat": False,
                },
            )
            expires_at = int(payload["exp"])
            user_id = UUID(str(payload["sub"]))
        except (jwt.InvalidTokenError, ValueError, TypeError) as error:
            raise InvalidToken() from error

        if expires_at <= now.timestamp():
            raise InvalidToken()
        return user_id
