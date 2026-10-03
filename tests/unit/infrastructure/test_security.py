from datetime import UTC, datetime, timedelta
from uuid import uuid7

import jwt
import pytest
from argon2.exceptions import InvalidHashError

from app.domain.exceptions import InvalidToken
from app.infrastructure.security.password_hasher import Argon2PasswordHasher
from app.infrastructure.security.token_service import JwtTokenService
from tests.factories import NOW

SECRET = "unit-test-secret-key-with-32-chars-or-more"


@pytest.fixture
def tokens() -> JwtTokenService:
    return JwtTokenService(secret_key=SECRET, expire_minutes=30)


@pytest.fixture(scope="module")
def hasher() -> Argon2PasswordHasher:
    return Argon2PasswordHasher()


class TestJwtTokenService:
    def test_round_trip(self, tokens):
        user_id = uuid7()

        issued = tokens.issue(user_id, now=NOW)

        assert tokens.decode(issued.access_token, now=NOW) == user_id
        assert issued.expires_in == 1800

    def test_carries_only_the_minimum_claims(self, tokens):
        issued = tokens.issue(uuid7(), now=NOW)

        claims = jwt.decode(issued.access_token, options={"verify_signature": False})

        assert set(claims) == {"sub", "iat", "exp"}

    def test_is_valid_until_it_expires(self, tokens):
        user_id = uuid7()
        token = tokens.issue(user_id, now=NOW).access_token

        assert tokens.decode(token, now=NOW + timedelta(minutes=29)) == user_id
        with pytest.raises(InvalidToken):
            tokens.decode(token, now=NOW + timedelta(minutes=30))

    def test_rejects_a_token_signed_with_another_key(self, tokens):
        forged = JwtTokenService(secret_key="x" * 40, expire_minutes=30)
        token = forged.issue(uuid7(), now=NOW).access_token

        with pytest.raises(InvalidToken):
            tokens.decode(token, now=NOW)

    @pytest.mark.parametrize(
        "claims",
        [
            {"iat": 0, "exp": 9_999_999_999},  # no subject
            {"sub": "not-a-uuid", "iat": 0, "exp": 9_999_999_999},
        ],
    )
    def test_rejects_tokens_with_bad_claims(self, tokens, claims):
        token = jwt.encode(claims, SECRET, algorithm="HS256")

        with pytest.raises(InvalidToken):
            tokens.decode(token, now=datetime.now(UTC))

    def test_rejects_garbage(self, tokens):
        with pytest.raises(InvalidToken):
            tokens.decode("not.a.jwt", now=NOW)


class TestArgon2PasswordHasher:
    def test_hashes_are_salted_argon2id(self, hasher):
        first, second = hasher.hash("correct-horse"), hasher.hash("correct-horse")

        assert first.startswith("$argon2id$")
        assert first != second

    def test_verifies_the_right_password_only(self, hasher):
        password_hash = hasher.hash("correct-horse")

        assert hasher.verify("correct-horse", password_hash)
        assert not hasher.verify("wrong-horse", password_hash)

    def test_an_unknown_user_never_matches(self, hasher):
        assert not hasher.verify("dummy-password-for-timing", None)

    def test_a_corrupted_hash_is_an_error_not_a_mismatch(self, hasher):
        with pytest.raises(InvalidHashError):
            hasher.verify("correct-horse", "not-an-argon2-hash")
