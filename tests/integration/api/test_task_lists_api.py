from tests.integration.api.conftest import assert_problem

LISTS = "/api/v1/lists"


def test_create_returns_201_with_location(client, owner):
    response = client.post(LISTS, json={"name": "  Groceries "}, headers=owner.headers)

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Groceries"
    assert response.headers["location"] == f"{LISTS}/{body['id']}"
    assert (
        client.get(response.headers["location"], headers=owner.headers).json() == body
    )


def test_lists_are_paginated_newest_first(client, owner):
    for name in ("First", "Second", "Third"):
        client.post(LISTS, json={"name": name}, headers=owner.headers)

    response = client.get(LISTS, params={"limit": 2}, headers=owner.headers)

    body = response.json()
    assert [item["name"] for item in body["items"]] == ["Third", "Second"]
    assert body["pagination"] == {"limit": 2, "offset": 0, "total": 3}


def test_rename_with_patch(client, owner, task_list):
    response = client.patch(
        f"{LISTS}/{task_list['id']}", json={"name": "Weekend"}, headers=owner.headers
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Weekend"


def test_patch_with_an_empty_body_changes_nothing(client, owner, task_list):
    response = client.patch(
        f"{LISTS}/{task_list['id']}", json={}, headers=owner.headers
    )

    assert response.json() == task_list


def test_patch_rejects_null_for_a_required_field(client, owner, task_list):
    response = client.patch(
        f"{LISTS}/{task_list['id']}", json={"name": None}, headers=owner.headers
    )

    body = assert_problem(response, 422, "VALIDATION_ERROR")
    assert body["errors"][0]["field"] == "name"


def test_blank_names_are_rejected_by_the_domain(client, owner):
    response = client.post(LISTS, json={"name": "   "}, headers=owner.headers)

    body = assert_problem(response, 422, "INVALID_FIELD_VALUE")
    assert body["errors"] == [{"field": "name", "message": "it cannot be empty."}]


def test_delete_removes_the_list_and_its_tasks(client, owner, task_list, task):
    response = client.delete(f"{LISTS}/{task_list['id']}", headers=owner.headers)

    assert response.status_code == 204
    assert response.content == b""
    assert_problem(
        client.get(f"{LISTS}/{task_list['id']}", headers=owner.headers),
        404,
        "TASK_LIST_NOT_FOUND",
    )
    assert_problem(
        client.get(f"/api/v1/tasks/{task['id']}", headers=owner.headers),
        404,
        "TASK_NOT_FOUND",
    )


def test_deleting_twice_returns_404(client, owner, task_list):
    client.delete(f"{LISTS}/{task_list['id']}", headers=owner.headers)

    response = client.delete(f"{LISTS}/{task_list['id']}", headers=owner.headers)

    assert_problem(response, 404, "TASK_LIST_NOT_FOUND")


def test_page_size_is_limited(client, owner):
    for limit in (0, 101):
        response = client.get(LISTS, params={"limit": limit}, headers=owner.headers)

        body = assert_problem(response, 422, "VALIDATION_ERROR")
        assert body["errors"][0]["field"] == "limit"
