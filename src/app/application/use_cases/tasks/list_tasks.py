from uuid import UUID

from app.application.dto import PageRequest, TaskFilters, TaskListing
from app.application.ports import TaskListRepository, TaskRepository
from app.application.use_cases.access import get_owned_list


class ListTasks:
    """Tasks of a list, filtered and paginated, plus the completion of the whole list.

    Filters only decide which tasks are shown; the completion always covers every task
    in the list (DEC-008).
    """

    def __init__(self, tasks: TaskRepository, task_lists: TaskListRepository) -> None:
        self._tasks = tasks
        self._task_lists = task_lists

    def execute(
        self,
        *,
        list_id: UUID,
        user_id: UUID,
        filters: TaskFilters,
        page: PageRequest,
    ) -> TaskListing:
        task_list = get_owned_list(self._task_lists, list_id, user_id)
        return TaskListing(
            page=self._tasks.list_by_list(task_list.id, filters, page),
            completion=self._tasks.completion_of(task_list.id),
        )
