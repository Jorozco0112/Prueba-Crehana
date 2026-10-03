import logging
from uuid import UUID

from app.application.ports import (
    Clock,
    TaskAssignmentNotifier,
    TaskListRepository,
    TaskRepository,
    UnitOfWork,
    UserRepository,
)
from app.application.use_cases.access import get_owned_task
from app.domain.exceptions import AssigneeNotFound, InvalidFieldValue
from app.domain.task import Task
from app.domain.user import User
from app.domain.value_objects import Email

logger = logging.getLogger(__name__)


class AssignTask:
    """Assign a responsible user by email and let them know (DEC-023, DEC-032, DEC-033).

    The notification is sent after the commit and on a best-effort basis: if it fails,
    the assignment is kept and the error is only logged.
    """

    def __init__(
        self,
        tasks: TaskRepository,
        task_lists: TaskListRepository,
        users: UserRepository,
        notifier: TaskAssignmentNotifier,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._tasks = tasks
        self._task_lists = task_lists
        self._users = users
        self._notifier = notifier
        self._uow = uow
        self._clock = clock

    def execute(self, *, task_id: UUID, user_id: UUID, assignee_email: str) -> Task:
        task, _ = get_owned_task(self._tasks, self._task_lists, task_id, user_id)

        try:
            assignee = self._users.get_by_email(Email(assignee_email))
        except InvalidFieldValue:
            assignee = None
        if assignee is None:
            raise AssigneeNotFound(assignee_email)

        if not task.assign_to(assignee.id, at=self._clock.now()):
            return task

        self._tasks.update(task)
        self._uow.commit()

        if assignee.id != user_id:
            self._notify(task, assignee)
        return task

    def _notify(self, task: Task, assignee: User) -> None:
        try:
            self._notifier.notify_assigned(task, assignee)
        except Exception:
            logger.exception(
                "Could not notify %s about task %s; the assignment was kept.",
                assignee.email,
                task.id,
            )
