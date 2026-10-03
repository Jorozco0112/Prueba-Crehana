from app.application.ports import Clock, PasswordHasher, UnitOfWork, UserRepository
from app.domain.exceptions import EmailAlreadyRegistered
from app.domain.rules import validate_password
from app.domain.user import User
from app.domain.value_objects import Email


class RegisterUser:
    def __init__(
        self,
        users: UserRepository,
        hasher: PasswordHasher,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._users = users
        self._hasher = hasher
        self._uow = uow
        self._clock = clock

    def execute(self, *, email: str, password: str, full_name: str) -> User:
        normalized_email = Email(email)
        validate_password(password)
        if self._users.get_by_email(normalized_email) is not None:
            raise EmailAlreadyRegistered(normalized_email.value)

        user = User.register(
            email=normalized_email,
            full_name=full_name,
            password_hash=self._hasher.hash(password),
            now=self._clock.now(),
        )
        # Two simultaneous registrations can both pass the check above; the
        # repository turns the UNIQUE violation into EmailAlreadyRegistered.
        self._users.add(user)
        self._uow.commit()
        return user
