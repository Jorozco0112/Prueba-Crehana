from uuid import UUID

from app.application.ports import Clock, TaskListRepository, UnitOfWork
from app.domain.task_list import TaskList


class CreateTaskList:
    def __init__(
        self, task_lists: TaskListRepository, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._task_lists = task_lists
        self._uow = uow
        self._clock = clock

    def execute(self, *, owner_id: UUID, name: str) -> TaskList:
        task_list = TaskList.create(owner_id=owner_id, name=name, now=self._clock.now())
        self._task_lists.add(task_list)
        self._uow.commit()
        return task_list
