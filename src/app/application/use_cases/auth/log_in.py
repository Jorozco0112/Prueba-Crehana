from app.application.dto import IssuedToken
from app.application.ports import Clock, PasswordHasher, TokenService, UserRepository
from app.domain.exceptions import InvalidCredentials, InvalidFieldValue
from app.domain.value_objects import Email


class LogIn:
    """Exchange email and password for an access token (DEC-030).

    Every failure raises the same error, so the response does not reveal whether the
    email is registered (DEC-031).
    """

    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        tokens: TokenService,
        clock: Clock,
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._tokens = tokens
        self._clock = clock

    def execute(self, *, email: str, password: str) -> IssuedToken:
        try:
            user = self._users.get_by_email(Email(email))
        except InvalidFieldValue:
            user = None

        password_hash = user.password_hash if user is not None else None
        password_matches = self._hasher.verify(password, password_hash)
        if user is None or not password_matches:
            raise InvalidCredentials()

        return self._tokens.issue(user.id, now=self._clock.now())
