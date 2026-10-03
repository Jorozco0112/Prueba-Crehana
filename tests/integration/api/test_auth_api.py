from tests.integration.api.conftest import PASSWORD, assert_problem, create_user

REGISTER = "/api/v1/auth/register"
LOGIN = "/api/v1/auth/login"


def test_register_returns_the_user_without_the_password(client):
    response = client.post(
        REGISTER,
        json={"email": "Ana@Example.com", "password": PASSWORD, "full_name": "Ana"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "ana@example.com"
    assert set(body) == {"id", "email", "full_name", "created_at"}


def test_register_twice_is_a_conflict(client):
    create_user(client, "ana@example.com")

    response = client.post(
        REGISTER,
        json={"email": "ANA@example.com", "password": PASSWORD, "full_name": "Ana"},
    )

    assert_problem(response, 409, "EMAIL_ALREADY_REGISTERED")


def test_register_validates_every_field(client):
    response = client.post(
        REGISTER,
        json={"email": "not-an-email", "password": "short", "full_name": "", "x": 1},
    )

    body = assert_problem(response, 422, "VALIDATION_ERROR")
    assert {error["field"] for error in body["errors"]} == {
        "email",
        "password",
        "full_name",
        "x",
    }


def test_login_returns_a_bearer_token(client):
    create_user(client, "ana@example.com")

    response = client.post(
        LOGIN, data={"username": "ana@example.com", "password": PASSWORD}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert body["expires_in"] == 30 * 60
    assert body["access_token"]


def test_wrong_password_and_unknown_email_get_the_same_answer(client):
    create_user(client, "ana@example.com")

    wrong_password = client.post(
        LOGIN, data={"username": "ana@example.com", "password": "wrong-password"}
    )
    unknown_email = client.post(
        LOGIN, data={"username": "nobody@example.com", "password": PASSWORD}
    )

    first = assert_problem(wrong_password, 401, "INVALID_CREDENTIALS")
    second = assert_problem(unknown_email, 401, "INVALID_CREDENTIALS")
    assert first == second
    assert wrong_password.headers["www-authenticate"] == "Bearer"


def test_protected_endpoints_require_a_token(client):
    response = client.get("/api/v1/lists")

    assert_problem(response, 401, "UNAUTHORIZED")
    assert response.headers["www-authenticate"] == "Bearer"


def test_an_invalid_token_is_rejected(client):
    response = client.get(
        "/api/v1/lists", headers={"Authorization": "Bearer not-a-real-token"}
    )

    assert_problem(response, 401, "INVALID_TOKEN")
