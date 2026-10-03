from uuid import UUID

from app.application.dto import TaskListChanges
from app.application.ports import Clock, TaskListRepository, UnitOfWork
from app.application.use_cases.access import get_owned_list
from app.domain.task_list import TaskList


class UpdateTaskList:
    def __init__(
        self, task_lists: TaskListRepository, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._task_lists = task_lists
        self._uow = uow
        self._clock = clock

    def execute(
        self, *, list_id: UUID, user_id: UUID, changes: TaskListChanges
    ) -> TaskList:
        task_list = get_owned_list(self._task_lists, list_id, user_id)
        if not changes:
            return task_list

        if "name" in changes:
            task_list.rename(changes["name"], at=self._clock.now())
        self._task_lists.update(task_list)
        self._uow.commit()
        return task_list
