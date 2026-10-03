from typing import Annotated

from fastapi import APIRouter, Depends

from app.application.use_cases.tasks.list_assigned_tasks import ListAssignedTasks
from app.entrypoints.api.dependencies import (
    CurrentUser,
    PageRequestDep,
    get_list_assigned_tasks,
)
from app.entrypoints.api.routers.responses import AUTHENTICATED
from app.entrypoints.api.schemas.tasks import TaskPageResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me/tasks", responses=AUTHENTICATED)
def list_my_tasks(
    user: CurrentUser,
    page: PageRequestDep,
    use_case: Annotated[ListAssignedTasks, Depends(get_list_assigned_tasks)],
) -> TaskPageResponse:
    """Tasks assigned to the current user, across every list."""
    return TaskPageResponse.from_page(use_case.execute(user_id=user.id, page=page))
