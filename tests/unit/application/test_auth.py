import pytest

from app.application.use_cases.auth.get_authenticated_user import GetAuthenticatedUser
from app.application.use_cases.auth.log_in import LogIn
from app.application.use_cases.auth.register_user import RegisterUser
from app.domain.exceptions import (
    EmailAlreadyRegistered,
    InvalidCredentials,
    InvalidFieldValue,
    InvalidToken,
)
from app.domain.value_objects import Email
from tests.factories import make_user


@pytest.fixture
def register(users, hasher, uow, clock) -> RegisterUser:
    return RegisterUser(users=users, hasher=hasher, uow=uow, clock=clock)


@pytest.fixture
def log_in(users, hasher, tokens, clock) -> LogIn:
    return LogIn(users=users, hasher=hasher, tokens=tokens, clock=clock)


@pytest.fixture
def authenticate(users, tokens, clock) -> GetAuthenticatedUser:
    return GetAuthenticatedUser(users=users, tokens=tokens, clock=clock)


class TestRegisterUser:
    def test_stores_the_user_with_a_hashed_password(self, register, users, uow, clock):
        user = register.execute(
            email="Ana@Example.com", password="correct-horse", full_name="Ana Torres"
        )

        stored = users.get(user.id)
        assert stored is not None
        assert stored.email == Email("ana@example.com")
        assert stored.password_hash == "hashed::correct-horse"
        assert stored.created_at == clock.now()
        assert uow.committed

    def test_rejects_an_email_already_registered_in_any_case(self, register, uow):
        register.execute(
            email="ana@example.com", password="correct-horse", full_name="Ana"
        )

        with pytest.raises(EmailAlreadyRegistered):
            register.execute(
                email="ANA@example.com", password="another-pass", full_name="Ana 2"
            )
        assert uow.commits == 1

    def test_rejects_a_short_password(self, register, uow):
        with pytest.raises(InvalidFieldValue) as error:
            register.execute(email="ana@example.com", password="short", full_name="A")

        assert error.value.field == "password"
        assert not uow.committed

    def test_rejects_an_invalid_email(self, register):
        with pytest.raises(InvalidFieldValue) as error:
            register.execute(
                email="not-an-email", password="long-enough", full_name="A"
            )

        assert error.value.field == "email"


class TestLogIn:
    def test_returns_a_token_for_valid_credentials(self, log_in, users, tokens, clock):
        user = make_user(email="ana@example.com", password_hash="hashed::correct-horse")
        users.add(user)

        issued = log_in.execute(email="ANA@example.com", password="correct-horse")

        assert tokens.decode(issued.access_token, now=clock.now()) == user.id
        assert issued.expires_in == 30 * 60

    def test_rejects_a_wrong_password(self, log_in, users):
        users.add(make_user(password_hash="hashed::correct-horse"))

        with pytest.raises(InvalidCredentials):
            log_in.execute(email="ana@example.com", password="wrong-password")

    def test_unknown_email_fails_the_same_way_and_still_checks_a_hash(
        self, log_in, hasher
    ):
        with pytest.raises(InvalidCredentials):
            log_in.execute(email="nobody@example.com", password="whatever-pass")

        # The dummy check keeps the response time from revealing unknown emails.
        assert hasher.verified == [None]

    def test_a_malformed_email_is_just_invalid_credentials(self, log_in):
        with pytest.raises(InvalidCredentials):
            log_in.execute(email="not-an-email", password="whatever-pass")


class TestGetAuthenticatedUser:
    def test_returns_the_user_of_a_valid_token(
        self, authenticate, users, tokens, clock
    ):
        user = make_user()
        users.add(user)
        token = tokens.issue(user.id, now=clock.now()).access_token

        assert authenticate.execute(token) == user

    def test_rejects_an_expired_token(self, authenticate, users, tokens, clock):
        user = make_user()
        users.add(user)
        token = tokens.issue(user.id, now=clock.now()).access_token
        clock.advance(minutes=31)

        with pytest.raises(InvalidToken):
            authenticate.execute(token)

    def test_rejects_a_token_whose_user_no_longer_exists(
        self, authenticate, tokens, clock
    ):
        token = tokens.issue(make_user().id, now=clock.now()).access_token

        with pytest.raises(InvalidToken):
            authenticate.execute(token)

    def test_rejects_a_malformed_token(self, authenticate):
        with pytest.raises(InvalidToken):
            authenticate.execute("not-a-token")
