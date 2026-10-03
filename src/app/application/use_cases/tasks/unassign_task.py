from uuid import UUID

from app.application.ports import Clock, TaskListRepository, TaskRepository, UnitOfWork
from app.application.use_cases.access import get_owned_task


class UnassignTask:
    """Remove the responsible user. No notification is sent (DEC-032)."""

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

    def execute(self, *, task_id: UUID, user_id: UUID) -> None:
        task, _ = get_owned_task(self._tasks, self._task_lists, task_id, user_id)
        if task.assignee_id is None:
            return

        task.unassign(at=self._clock.now())
        self._tasks.update(task)
        self._uow.commit()
