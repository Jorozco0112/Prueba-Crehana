from uuid import UUID

from app.application.dto import Page, PageRequest
from app.application.ports import TaskListRepository
from app.domain.task_list import TaskList


class ListTaskLists:
    def __init__(self, task_lists: TaskListRepository) -> None:
        self._task_lists = task_lists

    def execute(self, *, owner_id: UUID, page: PageRequest) -> Page[TaskList]:
        return self._task_lists.list_by_owner(owner_id, page)
