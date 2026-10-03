import pytest

from tests.integration.api.conftest import assert_problem


def tasks_url(task_list):
    return f"/api/v1/lists/{task_list['id']}/tasks"


def add_task(client, owner, task_list, **fields):
    response = client.post(tasks_url(task_list), json=fields, headers=owner.headers)
    assert response.status_code == 201, response.text
    return response.json()


def set_status(client, user, task, status):
    return client.put(
        f"/api/v1/tasks/{task['id']}/status",
        json={"status": status},
        headers=user.headers,
    )


class TestCreate:
    def test_defaults_and_location(self, client, owner, task_list):
        response = client.post(
            tasks_url(task_list), json={"title": "Buy milk"}, headers=owner.headers
        )

        assert response.status_code == 201
        task = response.json()
        assert task["status"] == "PENDING"
        assert task["priority"] == "MEDIUM"
        assert task["assignee_id"] is None
        assert task["completed_at"] is None
        assert response.headers["location"] == f"/api/v1/tasks/{task['id']}"

    def test_status_cannot_be_set_on_creation(self, client, owner, task_list):
        response = client.post(
            tasks_url(task_list),
            json={"title": "Done already", "status": "COMPLETED"},
            headers=owner.headers,
        )

        body = assert_problem(response, 422, "VALIDATION_ERROR")
        assert body["errors"][0]["field"] == "status"

    @pytest.mark.parametrize(
        ("payload", "field"),
        [
            ({"title": "x" * 201}, "title"),
            ({"title": "Buy milk", "priority": "SUPER_HIGH"}, "priority"),
            ({}, "title"),
        ],
    )
    def test_rejects_invalid_payloads(self, client, owner, task_list, payload, field):
        response = client.post(
            tasks_url(task_list), json=payload, headers=owner.headers
        )

        body = assert_problem(response, 422, "VALIDATION_ERROR")
        assert body["errors"][0]["field"] == field

    def test_a_blank_title_is_rejected_by_the_domain(self, client, owner, task_list):
        response = client.post(
            tasks_url(task_list), json={"title": "   "}, headers=owner.headers
        )

        assert_problem(response, 422, "INVALID_FIELD_VALUE")


class TestUpdate:
    def test_patch_changes_only_the_fields_sent(self, client, owner, task_list):
        task = add_task(client, owner, task_list, title="Buy milk", description="2L")

        response = client.patch(
            f"/api/v1/tasks/{task['id']}",
            json={"title": "Buy oat milk", "priority": "HIGH"},
            headers=owner.headers,
        )

        body = response.json()
        assert (body["title"], body["priority"]) == ("Buy oat milk", "HIGH")
        assert body["description"] == "2L"

    def test_description_null_clears_it(self, client, owner, task_list):
        task = add_task(client, owner, task_list, title="Buy milk", description="2L")

        response = client.patch(
            f"/api/v1/tasks/{task['id']}",
            json={"description": None},
            headers=owner.headers,
        )

        assert response.json()["description"] is None

    @pytest.mark.parametrize("field", ["title", "priority"])
    def test_required_fields_cannot_be_null(self, client, owner, task, field):
        response = client.patch(
            f"/api/v1/tasks/{task['id']}", json={field: None}, headers=owner.headers
        )

        body = assert_problem(response, 422, "VALIDATION_ERROR")
        assert body["errors"][0]["field"] == field

    def test_status_is_not_editable_with_patch(self, client, owner, task):
        response = client.patch(
            f"/api/v1/tasks/{task['id']}",
            json={"status": "COMPLETED"},
            headers=owner.headers,
        )

        assert_problem(response, 422, "VALIDATION_ERROR")

    def test_delete(self, client, owner, task):
        response = client.delete(f"/api/v1/tasks/{task['id']}", headers=owner.headers)

        assert response.status_code == 204
        assert_problem(
            client.get(f"/api/v1/tasks/{task['id']}", headers=owner.headers),
            404,
            "TASK_NOT_FOUND",
        )


class TestStatus:
    def test_completing_records_the_date_and_reopening_clears_it(
        self, client, owner, task
    ):
        completed = set_status(client, owner, task, "COMPLETED").json()
        reopened = set_status(client, owner, task, "PENDING").json()

        assert completed["status"] == "COMPLETED"
        assert completed["completed_at"] is not None
        assert reopened["completed_at"] is None

    def test_repeating_the_status_is_idempotent(self, client, owner, task):
        first = set_status(client, owner, task, "COMPLETED").json()
        second = set_status(client, owner, task, "COMPLETED").json()

        assert second == first

    def test_rejects_an_unknown_status(self, client, owner, task):
        response = set_status(client, owner, task, "ARCHIVED")

        assert_problem(response, 422, "VALIDATION_ERROR")


class TestListing:
    @pytest.fixture
    def populated(self, client, owner, task_list):
        created = {
            "low": add_task(client, owner, task_list, title="Low", priority="LOW"),
            "urgent": add_task(
                client, owner, task_list, title="Urgent", priority="URGENT"
            ),
            "high_done": add_task(
                client, owner, task_list, title="High done", priority="HIGH"
            ),
        }
        set_status(client, owner, created["high_done"], "COMPLETED")
        return created

    def test_completion_ignores_filters(self, client, owner, task_list, populated):
        response = client.get(
            tasks_url(task_list), params={"status": "PENDING"}, headers=owner.headers
        )

        body = response.json()
        assert [task["title"] for task in body["items"]] == ["Urgent", "Low"]
        assert body["pagination"]["total"] == 2
        assert body["completion"] == {
            "total_tasks": 3,
            "completed_tasks": 1,
            "percentage": 33.33,
        }

    def test_filter_by_priority(self, client, owner, task_list, populated):
        response = client.get(
            tasks_url(task_list), params={"priority": "HIGH"}, headers=owner.headers
        )

        assert [task["title"] for task in response.json()["items"]] == ["High done"]

    def test_orders_by_priority_and_paginates(
        self, client, owner, task_list, populated
    ):
        response = client.get(
            tasks_url(task_list),
            params={"limit": 2, "offset": 1},
            headers=owner.headers,
        )

        body = response.json()
        assert [task["title"] for task in body["items"]] == ["High done", "Low"]
        assert body["pagination"] == {"limit": 2, "offset": 1, "total": 3}

    def test_an_empty_list_is_at_zero_percent(self, client, owner, task_list):
        response = client.get(tasks_url(task_list), headers=owner.headers)

        assert response.json()["completion"] == {
            "total_tasks": 0,
            "completed_tasks": 0,
            "percentage": 0.0,
        }

    def test_rejects_an_unknown_filter_value(self, client, owner, task_list):
        response = client.get(
            tasks_url(task_list), params={"status": "DONE"}, headers=owner.headers
        )

        body = assert_problem(response, 422, "VALIDATION_ERROR")
        assert body["errors"][0]["field"] == "status"
