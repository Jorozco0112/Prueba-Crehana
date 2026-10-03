from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.application.dto import Page, TaskListing
from app.domain.rules import DESCRIPTION_MAX_LENGTH, TITLE_MAX_LENGTH
from app.domain.task import Task
from app.domain.value_objects import Priority, TaskStatus
from app.entrypoints.api.schemas.common import (
    PaginationMeta,
    RequestModel,
    ResponseModel,
)


class TaskCreateRequest(RequestModel):
    """No ``status`` field: tasks always start as PENDING (DEC-029)."""

    title: str = Field(min_length=1, max_length=TITLE_MAX_LENGTH)
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)
    priority: Priority = Priority.MEDIUM


class TaskUpdateRequest(RequestModel):
    """Partial update (DEC-022).

    An absent field is left unchanged; ``description: null`` clears the description;
    ``title`` and ``priority`` cannot be null.
    """

    title: str | None = Field(default=None, min_length=1, max_length=TITLE_MAX_LENGTH)
    description: str | None = Field(default=None, max_length=DESCRIPTION_MAX_LENGTH)
    priority: Priority | None = None

    @field_validator("title", "priority", mode="before")
    @classmethod
    def reject_null(cls, value: object) -> object:
        # Only runs when the client sends the field, so it tells `null` from absent.
        if value is None:
            raise ValueError("this field cannot be null")
        return value


class TaskStatusRequest(RequestModel):
    status: TaskStatus


class TaskAssigneeRequest(RequestModel):
    email: EmailStr


class TaskResponse(ResponseModel):
    id: UUID
    list_id: UUID
    title: str
    description: str | None
    priority: Priority
    status: TaskStatus
    assignee_id: UUID | None
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None


class CompletionResponse(BaseModel):
    total_tasks: int
    completed_tasks: int
    percentage: float


class TaskPageResponse(BaseModel):
    items: list[TaskResponse]
    pagination: PaginationMeta

    @classmethod
    def from_page(cls, page: Page[Task]) -> TaskPageResponse:
        return cls(
            items=[TaskResponse.model_validate(item) for item in page.items],
            pagination=PaginationMeta.from_page(page),
        )


class TaskPageWithCompletionResponse(TaskPageResponse):
    """``pagination.total`` counts the filtered tasks; ``completion`` counts every task
    in the list (DEC-024)."""

    completion: CompletionResponse

    @classmethod
    def from_listing(cls, listing: TaskListing) -> TaskPageWithCompletionResponse:
        page = TaskPageResponse.from_page(listing.page)
        return cls(
            items=page.items,
            pagination=page.pagination,
            completion=CompletionResponse(
                total_tasks=listing.completion.total,
                completed_tasks=listing.completion.completed,
                percentage=float(listing.completion.percentage),
            ),
        )
