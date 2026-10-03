from fastapi.testclient import TestClient

from app.entrypoints.api.dependencies import get_list_task_lists
from app.entrypoints.api.main import app
from tests.integration.api.conftest import assert_problem


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_unknown_routes_use_the_problem_format(client):
    assert_problem(client.get("/api/v1/nothing-here"), 404, "NOT_FOUND")


def test_unsupported_methods_use_the_problem_format(client):
    assert_problem(client.put("/api/v1/lists"), 405, "METHOD_NOT_ALLOWED")


def test_a_malformed_id_is_a_validation_error(client, owner):
    response = client.get("/api/v1/lists/not-a-uuid", headers=owner.headers)

    body = assert_problem(response, 422, "VALIDATION_ERROR")
    assert body["errors"][0]["field"] == "list_id"


def test_unexpected_errors_do_not_leak_details(engine, owner):
    def broken_use_case():
        raise RuntimeError("database password is hunter2")

    app.dependency_overrides[get_list_task_lists] = broken_use_case
    try:
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get("/api/v1/lists", headers=owner.headers)
    finally:
        app.dependency_overrides.clear()

    body = assert_problem(response, 500, "INTERNAL_ERROR")
    assert "hunter2" not in response.text
    assert body["detail"] == "An unexpected error occurred."
