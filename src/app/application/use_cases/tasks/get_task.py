from uuid import UUID

from app.application.ports import TaskListRepository, TaskRepository
from app.application.use_cases.access import get_visible_task
from app.domain.task import Task


class GetTask:
    """The owner of the list and the assignee can read a task."""

    def __init__(self, tasks: TaskRepository, task_lists: TaskListRepository) -> None:
        self._tasks = tasks
        self._task_lists = task_lists

    def execute(self, *, task_id: UUID, user_id: UUID) -> Task:
        task, _ = get_visible_task(self._tasks, self._task_lists, task_id, user_id)
        return task
