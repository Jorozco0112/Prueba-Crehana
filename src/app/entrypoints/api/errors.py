"""Translation of errors into HTTP responses (DEC-027 and DEC-028).

A single handler covers every domain error: it maps the error's category to a status
code, so adding a new error never requires changes here.
"""

import logging
from collections.abc import Mapping, Sequence
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.domain.exceptions import (
    AuthenticationError,
    BusinessRuleViolation,
    ConflictError,
    DomainError,
    InvalidFieldValue,
    NotFoundError,
    PermissionDeniedError,
)

logger = logging.getLogger(__name__)

STATUS_BY_CATEGORY: dict[type[DomainError], int] = {
    NotFoundError: HTTPStatus.NOT_FOUND,
    PermissionDeniedError: HTTPStatus.FORBIDDEN,
    ConflictError: HTTPStatus.CONFLICT,
    BusinessRuleViolation: HTTPStatus.UNPROCESSABLE_CONTENT,
    AuthenticationError: HTTPStatus.UNAUTHORIZED,
}

_REQUEST_PARTS = {"body", "query", "path", "header", "cookie"}


def problem_response(
    status: int,
    detail: str,
    code: str,
    *,
    errors: list[dict[str, str]] | None = None,
    headers: Mapping[str, str] | None = None,
) -> JSONResponse:
    content: dict[str, Any] = {
        "title": HTTPStatus(status).phrase,
        "status": status,
        "detail": detail,
        "code": code,
    }
    if errors is not None:
        content["errors"] = errors
    return JSONResponse(
        content,
        status_code=status,
        headers=headers,
        media_type="application/problem+json",
    )


def status_for(error: DomainError) -> int:
    for category in type(error).__mro__:
        if category in STATUS_BY_CATEGORY:
            return STATUS_BY_CATEGORY[category]
    return HTTPStatus.INTERNAL_SERVER_ERROR


async def handle_domain_error(request: Request, error: DomainError) -> JSONResponse:
    status = status_for(error)
    headers = (
        {"WWW-Authenticate": "Bearer"} if status == HTTPStatus.UNAUTHORIZED else None
    )
    errors = None
    if isinstance(error, InvalidFieldValue):
        errors = [{"field": error.field, "message": error.reason}]
    return problem_response(
        status, error.message, error.code, errors=errors, headers=headers
    )


async def handle_validation_error(
    request: Request, error: RequestValidationError
) -> JSONResponse:
    errors = [
        {"field": _field_name(item["loc"]), "message": item["msg"]}
        for item in error.errors()
    ]
    return problem_response(
        HTTPStatus.UNPROCESSABLE_CONTENT,
        "The request contains invalid fields.",
        "VALIDATION_ERROR",
        errors=errors,
    )


async def handle_http_exception(
    request: Request, error: StarletteHTTPException
) -> JSONResponse:
    return problem_response(
        error.status_code,
        str(error.detail),
        HTTPStatus(error.status_code).name,
        headers=error.headers,
    )


async def handle_unexpected_error(request: Request, error: Exception) -> JSONResponse:
    # The stack trace goes to the log only; clients never see internal details.
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return problem_response(
        HTTPStatus.INTERNAL_SERVER_ERROR,
        "An unexpected error occurred.",
        "INTERNAL_ERROR",
    )


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(
        DomainError, handle_domain_error  # type: ignore[arg-type]
    )
    app.add_exception_handler(
        RequestValidationError, handle_validation_error  # type: ignore[arg-type]
    )
    app.add_exception_handler(
        StarletteHTTPException, handle_http_exception  # type: ignore[arg-type]
    )
    app.add_exception_handler(Exception, handle_unexpected_error)


def _field_name(location: Sequence[int | str]) -> str:
    parts = [str(part) for part in location]
    if len(parts) > 1 and parts[0] in _REQUEST_PARTS:
        parts = parts[1:]
    return ".".join(parts)
