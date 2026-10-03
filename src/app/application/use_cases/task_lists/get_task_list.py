from uuid import UUID

from app.application.ports import TaskListRepository
from app.application.use_cases.access import get_owned_list
from app.domain.task_list import TaskList


class GetTaskList:
    def __init__(self, task_lists: TaskListRepository) -> None:
        self._task_lists = task_lists

    def execute(self, *, list_id: UUID, user_id: UUID) -> TaskList:
        return get_owned_list(self._task_lists, list_id, user_id)
