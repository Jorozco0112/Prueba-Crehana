from typing import Annotated, cast
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.application.dto import TaskChanges
from app.application.use_cases.tasks.assign_task import AssignTask
from app.application.use_cases.tasks.change_task_status import ChangeTaskStatus
from app.application.use_cases.tasks.delete_task import DeleteTask
from app.application.use_cases.tasks.get_task import GetTask
from app.application.use_cases.tasks.unassign_task import UnassignTask
from app.application.use_cases.tasks.update_task import UpdateTask
from app.entrypoints.api.dependencies import (
    CurrentUser,
    get_assign_task,
    get_change_task_status,
    get_delete_task,
    get_get_task,
    get_unassign_task,
    get_update_task,
)
from app.entrypoints.api.routers.responses import OWNED_RESOURCE, TASK_RESOURCE
from app.entrypoints.api.schemas.tasks import (
    TaskAssigneeRequest,
    TaskResponse,
    TaskStatusRequest,
    TaskUpdateRequest,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/{task_id}", responses=OWNED_RESOURCE)
def get_task(
    task_id: UUID,
    user: CurrentUser,
    use_case: Annotated[GetTask, Depends(get_get_task)],
) -> TaskResponse:
    """Visible to the owner of the list and to the assignee."""
    return TaskResponse.model_validate(
        use_case.execute(task_id=task_id, user_id=user.id)
    )


@router.patch("/{task_id}", responses=TASK_RESOURCE)
def update_task(
    task_id: UUID,
    body: TaskUpdateRequest,
    user: CurrentUser,
    use_case: Annotated[UpdateTask, Depends(get_update_task)],
) -> TaskResponse:
    """Partial update of title, description and priority. Owner only."""
    changes = cast(TaskChanges, body.model_dump(exclude_unset=True))
    task = use_case.execute(task_id=task_id, user_id=user.id, changes=changes)
    return TaskResponse.model_validate(task)


@router.delete(
    "/{task_id}", status_code=status.HTTP_204_NO_CONTENT, responses=TASK_RESOURCE
)
def delete_task(
    task_id: UUID,
    user: CurrentUser,
    use_case: Annotated[DeleteTask, Depends(get_delete_task)],
) -> None:
    use_case.execute(task_id=task_id, user_id=user.id)


@router.put("/{task_id}/status", responses=OWNED_RESOURCE)
def change_task_status(
    task_id: UUID,
    body: TaskStatusRequest,
    user: CurrentUser,
    use_case: Annotated[ChangeTaskStatus, Depends(get_change_task_status)],
) -> TaskResponse:
    """Owner or assignee. Idempotent: repeating the current status changes nothing."""
    task = use_case.execute(task_id=task_id, user_id=user.id, status=body.status)
    return TaskResponse.model_validate(task)


@router.put("/{task_id}/assignee", responses=TASK_RESOURCE)
def assign_task(
    task_id: UUID,
    body: TaskAssigneeRequest,
    user: CurrentUser,
    use_case: Annotated[AssignTask, Depends(get_assign_task)],
) -> TaskResponse:
    """Assign the task to the registered user with this email and notify them."""
    task = use_case.execute(task_id=task_id, user_id=user.id, assignee_email=body.email)
    return TaskResponse.model_validate(task)


@router.delete(
    "/{task_id}/assignee",
    status_code=status.HTTP_204_NO_CONTENT,
    responses=TASK_RESOURCE,
)
def unassign_task(
    task_id: UUID,
    user: CurrentUser,
    use_case: Annotated[UnassignTask, Depends(get_unassign_task)],
) -> None:
    use_case.execute(task_id=task_id, user_id=user.id)
