from uuid import UUID

from app.application.dto import Page, PageRequest
from app.application.ports import TaskRepository
from app.domain.task import Task


class ListAssignedTasks:
    """Tasks assigned to the current user, without access to the rest of the list."""

    def __init__(self, tasks: TaskRepository) -> None:
        self._tasks = tasks

    def execute(self, *, user_id: UUID, page: PageRequest) -> Page[Task]:
        return self._tasks.list_by_assignee(user_id, page)
