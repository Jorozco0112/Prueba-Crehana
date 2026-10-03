from pydantic import BaseModel, ConfigDict

from app.application.dto import Page


class RequestModel(BaseModel):
    """Unknown fields are rejected instead of silently ignored (DEC-029)."""

    model_config = ConfigDict(extra="forbid")


class ResponseModel(BaseModel):
    """Built straight from domain entities (DEC-012)."""

    model_config = ConfigDict(from_attributes=True)


class PaginationMeta(BaseModel):
    limit: int
    offset: int
    total: int

    @classmethod
    def from_page[T](cls, page: Page[T]) -> PaginationMeta:
        return cls(limit=page.limit, offset=page.offset, total=page.total)


class FieldError(BaseModel):
    field: str
    message: str


class ProblemDetails(BaseModel):
    """Error format shared by every endpoint (RFC 9457, DEC-028)."""

    title: str
    status: int
    detail: str
    code: str
    errors: list[FieldError] | None = None
