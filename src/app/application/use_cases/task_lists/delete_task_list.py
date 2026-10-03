from uuid import UUID

from app.application.ports import TaskListRepository, UnitOfWork
from app.application.use_cases.access import get_owned_list


class DeleteTaskList:
    """Delete a list. Its tasks are removed by the database (ON DELETE CASCADE)."""

    def __init__(self, task_lists: TaskListRepository, uow: UnitOfWork) -> None:
        self._task_lists = task_lists
        self._uow = uow

    def execute(self, *, list_id: UUID, user_id: UUID) -> None:
        task_list = get_owned_list(self._task_lists, list_id, user_id)
        self._task_lists.delete(task_list)
        self._uow.commit()
