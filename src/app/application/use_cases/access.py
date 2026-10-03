"""Access rules shared by the use cases (DEC-002 and DEC-026).

- What a user cannot see answers "not found", as if it did not exist.
- What a user can see but cannot modify answers "permission denied".
"""

from uuid import UUID

from app.application.ports import TaskListRepository, TaskRepository
from app.domain.exceptions import NotTaskOwner, TaskListNotFound, TaskNotFound
from app.domain.task import Task
from app.domain.task_list import TaskList


def get_owned_list(
    task_lists: TaskListRepository, list_id: UUID, user_id: UUID
) -> TaskList:
    """Only the owner can see a list."""
    task_list = task_lists.get(list_id)
    if task_list is None or not task_list.is_owned_by(user_id):
        raise TaskListNotFound(list_id)
    return task_list


def get_visible_task(
    tasks: TaskRepository,
    task_lists: TaskListRepository,
    task_id: UUID,
    user_id: UUID,
) -> tuple[Task, TaskList]:
    """The owner of the list and the assignee can see a task."""
    task = tasks.get(task_id)
    if task is None:
        raise TaskNotFound(task_id)
    task_list = task_lists.get(task.list_id)
    if task_list is None:
        raise TaskNotFound(task_id)
    if not task_list.is_owned_by(user_id) and not task.is_assigned_to(user_id):
        raise TaskNotFound(task_id)
    return task, task_list


def get_owned_task(
    tasks: TaskRepository,
    task_lists: TaskListRepository,
    task_id: UUID,
    user_id: UUID,
) -> tuple[Task, TaskList]:
    """Only the owner can modify a task; the assignee can see it, so they get a 403."""
    task, task_list = get_visible_task(tasks, task_lists, task_id, user_id)
    if not task_list.is_owned_by(user_id):
        raise NotTaskOwner(task_id)
    return task, task_list
