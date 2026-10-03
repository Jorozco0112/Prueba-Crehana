from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from app.application.dto import Page
from app.domain.rules import LIST_NAME_MAX_LENGTH
from app.domain.task_list import TaskList
from app.entrypoints.api.schemas.common import (
    PaginationMeta,
    RequestModel,
    ResponseModel,
)


class TaskListCreateRequest(RequestModel):
    name: str = Field(min_length=1, max_length=LIST_NAME_MAX_LENGTH)


class TaskListUpdateRequest(RequestModel):
    """Partial update: absent fields are left unchanged (DEC-022)."""

    name: str | None = Field(
        default=None, min_length=1, max_length=LIST_NAME_MAX_LENGTH
    )

    @field_validator("name", mode="before")
    @classmethod
    def reject_null(cls, value: object) -> object:
        # Only runs when the client sends the field, so it tells `null` from absent.
        if value is None:
            raise ValueError("this field cannot be null")
        return value


class TaskListResponse(ResponseModel):
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime


class TaskListPageResponse(BaseModel):
    items: list[TaskListResponse]
    pagination: PaginationMeta

    @classmethod
    def from_page(cls, page: Page[TaskList]) -> TaskListPageResponse:
        return cls(
            items=[TaskListResponse.model_validate(item) for item in page.items],
            pagination=PaginationMeta.from_page(page),
        )
