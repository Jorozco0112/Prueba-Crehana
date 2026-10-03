"""The permission table of DEC-002, as an executable test (DEC-034).

- What a user cannot see answers 404, as if it did not exist (DEC-026).
- What a user can see but cannot modify answers 403.
"""

import pytest

LIST = "/api/v1/lists/{list_id}"
TASK = "/api/v1/tasks/{task_id}"

ACTIONS = {
    "get list": ("GET", LIST, None),
    "rename list": ("PATCH", LIST, {"name": "Renamed"}),
    "delete list": ("DELETE", LIST, None),
    "create task": ("POST", LIST + "/tasks", {"title": "New task"}),
    "list tasks": ("GET", LIST + "/tasks", None),
    "get task": ("GET", TASK, None),
    "edit task": ("PATCH", TASK, {"title": "Edited"}),
    "delete task": ("DELETE", TASK, None),
    "change status": ("PUT", TASK + "/status", {"status": "COMPLETED"}),
    "assign": ("PUT", TASK + "/assignee", {"email": "stranger@example.com"}),
    "unassign": ("DELETE", TASK + "/assignee", None),
}

#                 action:          owner, assignee, stranger
EXPECTED = {
    "get list": (200, 404, 404),
    "rename list": (200, 404, 404),
    "delete list": (204, 404, 404),
    "create task": (201, 404, 404),
    "list tasks": (200, 404, 404),
    "get task": (200, 200, 404),
    "edit task": (200, 403, 404),
    "delete task": (204, 403, 404),
    "change status": (200, 200, 404),
    "assign": (200, 403, 404),
    "unassign": (204, 403, 404),
}

ACTORS = ("owner", "assignee", "stranger")


@pytest.mark.parametrize("actor_index", range(3), ids=ACTORS)
@pytest.mark.parametrize("action", ACTIONS)
def test_permission_matrix(
    request,
    client,
    owner,
    assignee,
    stranger,
    task_list,
    assigned_task,
    action,
    actor_index,
):
    method, template, payload = ACTIONS[action]
    actor = request.getfixturevalue(ACTORS[actor_index])
    url = template.format(list_id=task_list["id"], task_id=assigned_task["id"])

    response = client.request(method, url, json=payload, headers=actor.headers)

    assert response.status_code == EXPECTED[action][actor_index], response.text
