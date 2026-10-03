from uuid import UUID

from app.application.ports import TaskListRepository, TaskRepository, UnitOfWork
from app.application.use_cases.access import get_owned_task


class DeleteTask:
    def __init__(
        self, tasks: TaskRepository, task_lists: TaskListRepository, uow: UnitOfWork
    ) -> None:
        self._tasks = tasks
        self._task_lists = task_lists
        self._uow = uow

    def execute(self, *, task_id: UUID, user_id: UUID) -> None:
        task, _ = get_owned_task(self._tasks, self._task_lists, task_id, user_id)
        self._tasks.delete(task)
        self._uow.commit()
