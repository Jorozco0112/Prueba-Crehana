from app.application.ports import Clock, TokenService, UserRepository
from app.domain.exceptions import InvalidToken
from app.domain.user import User


class GetAuthenticatedUser:
    """Resolve an access token to its user.

    The user is loaded from the database on every request, so a token whose user no
    longer exists gets a 401 instead of failing later (DEC-030).
    """

    def __init__(
        self, users: UserRepository, tokens: TokenService, clock: Clock
    ) -> None:
        self._users = users
        self._tokens = tokens
        self._clock = clock

    def execute(self, token: str) -> User:
        user_id = self._tokens.decode(token, now=self._clock.now())
        user = self._users.get(user_id)
        if user is None:
            raise InvalidToken()
        return user
