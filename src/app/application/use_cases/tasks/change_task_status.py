from uuid import UUID

from app.application.ports import Clock, TaskListRepository, TaskRepository, UnitOfWork
from app.application.use_cases.access import get_visible_task
from app.domain.task import Task
from app.domain.value_objects import TaskStatus


class ChangeTaskStatus:
    """Both the owner and the assignee can change the status (DEC-002)."""

    def __init__(
        self,
        tasks: TaskRepository,
        task_lists: TaskListRepository,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._tasks = tasks
        self._task_lists = task_lists
        self._uow = uow
        self._clock = clock

    def execute(self, *, task_id: UUID, user_id: UUID, status: TaskStatus) -> Task:
        task, _ = get_visible_task(self._tasks, self._task_lists, task_id, user_id)
        if task.status == status:
            return task

        task.change_status(status, at=self._clock.now())
        self._tasks.update(task)
        self._uow.commit()
        return task
