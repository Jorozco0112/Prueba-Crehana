from tests.integration.api.conftest import assert_problem


def assign(client, owner, task, email):
    return client.put(
        f"/api/v1/tasks/{task['id']}/assignee",
        json={"email": email},
        headers=owner.headers,
    )


def test_assigning_by_email_notifies_the_assignee(
    client, notifier, owner, assignee, task
):
    response = assign(client, owner, task, "ASSIGNEE@example.com")

    assert response.status_code == 200
    assert response.json()["assignee_id"] == assignee.id
    [(notified_task, notified_user)] = notifier.sent
    assert str(notified_task.id) == task["id"]
    assert notified_user.email.value == assignee.email


def test_the_assignee_sees_and_works_on_the_task(client, assignee, assigned_task):
    my_tasks = client.get("/api/v1/users/me/tasks", headers=assignee.headers).json()
    started = client.put(
        f"/api/v1/tasks/{assigned_task['id']}/status",
        json={"status": "IN_PROGRESS"},
        headers=assignee.headers,
    )

    assert [task["id"] for task in my_tasks["items"]] == [assigned_task["id"]]
    assert my_tasks["pagination"]["total"] == 1
    assert started.json()["status"] == "IN_PROGRESS"


def test_assigning_the_same_user_twice_notifies_once(
    client, notifier, owner, assignee, task
):
    assign(client, owner, task, assignee.email)
    assign(client, owner, task, assignee.email)

    assert len(notifier.sent) == 1


def test_the_owner_assigning_themselves_gets_no_email(client, notifier, owner, task):
    response = assign(client, owner, task, owner.email)

    assert response.json()["assignee_id"] == owner.id
    assert notifier.sent == []


def test_an_unregistered_email_is_rejected(client, owner, task):
    response = assign(client, owner, task, "nobody@example.com")

    assert_problem(response, 422, "ASSIGNEE_NOT_FOUND")


def test_unassigning_removes_the_assignees_access(
    client, owner, assignee, assigned_task
):
    response = client.delete(
        f"/api/v1/tasks/{assigned_task['id']}/assignee", headers=owner.headers
    )

    assert response.status_code == 204
    assert_problem(
        client.get(f"/api/v1/tasks/{assigned_task['id']}", headers=assignee.headers),
        404,
        "TASK_NOT_FOUND",
    )
    my_tasks = client.get("/api/v1/users/me/tasks", headers=assignee.headers).json()
    assert my_tasks["items"] == []
