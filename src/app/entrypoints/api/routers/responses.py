"""Error responses documented in OpenAPI for each group of endpoints."""

from typing import Any

from app.entrypoints.api.schemas.common import ProblemDetails

_PROBLEM: dict[str, Any] = {"model": ProblemDetails}

AUTHENTICATED: dict[int | str, dict[str, Any]] = {
    401: {**_PROBLEM, "description": "Missing, invalid or expired token"},
    422: {**_PROBLEM, "description": "Invalid request"},
}
OWNED_RESOURCE: dict[int | str, dict[str, Any]] = {
    **AUTHENTICATED,
    404: {**_PROBLEM, "description": "Not found or not visible to the user"},
}
TASK_RESOURCE: dict[int | str, dict[str, Any]] = {
    **OWNED_RESOURCE,
    403: {
        **_PROBLEM,
        "description": "Visible to the user, but only the owner can do it",
    },
}
