from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, Response, status

from app.application.dto import TaskFilters, TaskListChanges
from app.application.use_cases.task_lists.create_task_list import CreateTaskList
from app.application.use_cases.task_lists.delete_task_list import DeleteTaskList
from app.application.use_cases.task_lists.get_task_list import GetTaskList
from app.application.use_cases.task_lists.list_task_lists import ListTaskLists
from app.application.use_cases.task_lists.update_task_list import UpdateTaskList
from app.application.use_cases.tasks.create_task import CreateTask
from app.application.use_cases.tasks.list_tasks import ListTasks
from app.domain.value_objects import Priority, TaskStatus
from app.entrypoints.api.dependencies import (
    CurrentUser,
    PageRequestDep,
    get_create_task,
    get_create_task_list,
    get_delete_task_list,
    get_get_task_list,
    get_list_task_lists,
    get_list_tasks,
    get_update_task_list,
)
from app.entrypoints.api.routers.responses import AUTHENTICATED, OWNED_RESOURCE
from app.entrypoints.api.schemas.task_lists import (
    TaskListCreateRequest,
    TaskListPageResponse,
    TaskListResponse,
    TaskListUpdateRequest,
)
from app.entrypoints.api.schemas.tasks import (
    TaskCreateRequest,
    TaskPageWithCompletionResponse,
    TaskResponse,
)

router = APIRouter(prefix="/lists", tags=["task lists"])


@router.post("", status_code=status.HTTP_201_CREATED, responses=AUTHENTICATED)
def create_task_list(
    body: TaskListCreateRequest,
    request: Request,
    response: Response,
    user: CurrentUser,
    use_case: Annotated[CreateTaskList, Depends(get_create_task_list)],
) -> TaskListResponse:
    task_list = use_case.execute(owner_id=user.id, name=body.name)
    response.headers["Location"] = str(
        request.app.url_path_for("get_task_list", list_id=str(task_list.id))
    )
    return TaskListResponse.model_validate(task_list)


@router.get("", responses=AUTHENTICATED)
def list_task_lists(
    user: CurrentUser,
    page: PageRequestDep,
    use_case: Annotated[ListTaskLists, Depends(get_list_task_lists)],
) -> TaskListPageResponse:
    """Lists owned by the current user, newest first."""
    return TaskListPageResponse.from_page(use_case.execute(owner_id=user.id, page=page))


@router.get("/{list_id}", responses=OWNED_RESOURCE)
def get_task_list(
    list_id: UUID,
    user: CurrentUser,
    use_case: Annotated[GetTaskList, Depends(get_get_task_list)],
) -> TaskListResponse:
    task_list = use_case.execute(list_id=list_id, user_id=user.id)
    return TaskListResponse.model_validate(task_list)


@router.patch("/{list_id}", responses=OWNED_RESOURCE)
def update_task_list(
    list_id: UUID,
    body: TaskListUpdateRequest,
    user: CurrentUser,
    use_case: Annotated[UpdateTaskList, Depends(get_update_task_list)],
) -> TaskListResponse:
    changes = cast(TaskListChanges, body.model_dump(exclude_unset=True))
    task_list = use_case.execute(list_id=list_id, user_id=user.id, changes=changes)
    return TaskListResponse.model_validate(task_list)


@router.delete(
    "/{list_id}", status_code=status.HTTP_204_NO_CONTENT, responses=OWNED_RESOURCE
)
def delete_task_list(
    list_id: UUID,
    user: CurrentUser,
    use_case: Annotated[DeleteTaskList, Depends(get_delete_task_list)],
) -> None:
    """Deletes the list and all its tasks."""
    use_case.execute(list_id=list_id, user_id=user.id)


@router.post(
    "/{list_id}/tasks",
    status_code=status.HTTP_201_CREATED,
    responses=OWNED_RESOURCE,
    tags=["tasks"],
)
def create_task(
    list_id: UUID,
    body: TaskCreateRequest,
    request: Request,
    response: Response,
    user: CurrentUser,
    use_case: Annotated[CreateTask, Depends(get_create_task)],
) -> TaskResponse:
    task = use_case.execute(
        list_id=list_id,
        user_id=user.id,
        title=body.title,
        description=body.description,
        priority=body.priority,
    )
    response.headers["Location"] = str(
        request.app.url_path_for("get_task", task_id=str(task.id))
    )
    return TaskResponse.model_validate(task)


@router.get("/{list_id}/tasks", responses=OWNED_RESOURCE, tags=["tasks"])
def list_tasks(
    list_id: UUID,
    user: CurrentUser,
    page: PageRequestDep,
    use_case: Annotated[ListTasks, Depends(get_list_tasks)],
    task_status: Annotated[TaskStatus | None, Query(alias="status")] = None,
    priority: Priority | None = None,
) -> TaskPageWithCompletionResponse:
    """Tasks of a list with optional filters, plus the completion of the whole list.

    Filters narrow the tasks shown and ``pagination.total``; ``completion`` always
    covers every task in the list.
    """
    listing = use_case.execute(
        list_id=list_id,
        user_id=user.id,
        filters=TaskFilters(status=task_status, priority=priority),
        page=page,
    )
    return TaskPageWithCompletionResponse.from_listing(listing)
