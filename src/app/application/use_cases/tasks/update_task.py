from uuid import UUID

from app.application.dto import TaskChanges
from app.application.ports import Clock, TaskListRepository, TaskRepository, UnitOfWork
from app.application.use_cases.access import get_owned_task
from app.domain.task import Task


class UpdateTask:
    """Edit title, description and priority. Only the owner can do it (DEC-002)."""

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

    def execute(self, *, task_id: UUID, user_id: UUID, changes: TaskChanges) -> Task:
        task, _ = get_owned_task(self._tasks, self._task_lists, task_id, user_id)
        if not changes:
            return task

        now = self._clock.now()
        if "title" in changes:
            task.rename(changes["title"], at=now)
        if "description" in changes:
            task.describe(changes["description"], at=now)
        if "priority" in changes:
            task.prioritize(changes["priority"], at=now)
        self._tasks.update(task)
        self._uow.commit()
        return task
