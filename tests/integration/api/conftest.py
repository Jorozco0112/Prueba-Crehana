from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.entrypoints.api.dependencies import get_notifier
from app.entrypoints.api.main import app
from tests.fakes import InMemoryNotifier

PASSWORD = "correct-horse-battery"


@dataclass
class ApiUser:
    email: str
    headers: dict[str, str]
    id: str


@pytest.fixture
def notifier() -> InMemoryNotifier:
    return InMemoryNotifier()


@pytest.fixture
def client(engine, notifier) -> Iterator[TestClient]:
    app.dependency_overrides[get_notifier] = lambda: notifier
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def create_user(
    client: TestClient, email: str, full_name: str = "Test User"
) -> ApiUser:
    registered = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": PASSWORD, "full_name": full_name},
    )
    assert registered.status_code == 201, registered.text
    logged_in = client.post(
        "/api/v1/auth/login", data={"username": email, "password": PASSWORD}
    )
    assert logged_in.status_code == 200, logged_in.text
    token = logged_in.json()["access_token"]
    return ApiUser(
        email=email,
        headers={"Authorization": f"Bearer {token}"},
        id=registered.json()["id"],
    )


@pytest.fixture
def owner(client) -> ApiUser:
    return create_user(client, "owner@example.com", "Olivia Owner")


@pytest.fixture
def assignee(client) -> ApiUser:
    return create_user(client, "assignee@example.com", "Adam Assignee")


@pytest.fixture
def stranger(client) -> ApiUser:
    return create_user(client, "stranger@example.com", "Sam Stranger")


@pytest.fixture
def task_list(client, owner) -> dict[str, Any]:
    response = client.post(
        "/api/v1/lists", json={"name": "Groceries"}, headers=owner.headers
    )
    assert response.status_code == 201
    body: dict[str, Any] = response.json()
    return body


@pytest.fixture
def task(client, owner, task_list) -> dict[str, Any]:
    response = client.post(
        f"/api/v1/lists/{task_list['id']}/tasks",
        json={"title": "Buy milk"},
        headers=owner.headers,
    )
    assert response.status_code == 201
    body: dict[str, Any] = response.json()
    return body


@pytest.fixture
def assigned_task(client, owner, assignee, task) -> dict[str, Any]:
    response = client.put(
        f"/api/v1/tasks/{task['id']}/assignee",
        json={"email": assignee.email},
        headers=owner.headers,
    )
    assert response.status_code == 200
    body: dict[str, Any] = response.json()
    return body


def assert_problem(response: Any, status: int, code: str) -> dict[str, Any]:
    """Every error uses the same Problem Details format (DEC-028)."""
    assert response.status_code == status, response.text
    assert response.headers["content-type"] == "application/problem+json"
    body: dict[str, Any] = response.json()
    assert body["status"] == status
    assert body["code"] == code
    assert body["title"] and body["detail"]
    return body
