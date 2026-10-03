from uuid import UUID

from app.application.ports import Clock, TaskListRepository, TaskRepository, UnitOfWork
from app.application.use_cases.access import get_owned_list
from app.domain.task import Task
from app.domain.value_objects import Priority


class CreateTask:
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

    def execute(
        self,
        *,
        list_id: UUID,
        user_id: UUID,
        title: str,
        description: str | None = None,
        priority: Priority = Priority.MEDIUM,
    ) -> Task:
        task_list = get_owned_list(self._task_lists, list_id, user_id)
        task = Task.create(
            list_id=task_list.id,
            title=title,
            description=description,
            priority=priority,
            now=self._clock.now(),
        )
        self._tasks.add(task)
        self._uow.commit()
        return task
