"""Domain errors.

Errors are grouped in categories (DEC-027). The domain only states *what* went wrong
("not found", "conflict"); the HTTP layer decides how to communicate it.
"""

from typing import ClassVar
from uuid import UUID


class DomainError(Exception):
    """Base class for every error raised by the domain and the use cases."""

    code: ClassVar[str] = "DOMAIN_ERROR"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


# --- Categories -------------------------------------------------------------------


class NotFoundError(DomainError):
    """The resource does not exist or the user is not allowed to see it."""


class PermissionDeniedError(DomainError):
    """The user can see the resource but cannot perform the action."""


class ConflictError(DomainError):
    """The action conflicts with the current state of the system."""


class BusinessRuleViolation(DomainError):
    """The request is well formed but breaks a business rule."""


class AuthenticationError(DomainError):
    """The caller could not be authenticated."""


# --- Not found --------------------------------------------------------------------


class TaskListNotFound(NotFoundError):
    code = "TASK_LIST_NOT_FOUND"

    def __init__(self, list_id: UUID) -> None:
        super().__init__(f"Task list '{list_id}' was not found.")


class TaskNotFound(NotFoundError):
    code = "TASK_NOT_FOUND"

    def __init__(self, task_id: UUID) -> None:
        super().__init__(f"Task '{task_id}' was not found.")


# --- Permission denied ------------------------------------------------------------


class NotTaskOwner(PermissionDeniedError):
    code = "NOT_TASK_OWNER"

    def __init__(self, task_id: UUID) -> None:
        super().__init__(f"Only the owner of the list can modify task '{task_id}'.")


# --- Conflict ---------------------------------------------------------------------


class EmailAlreadyRegistered(ConflictError):
    code = "EMAIL_ALREADY_REGISTERED"

    def __init__(self, email: str) -> None:
        super().__init__(f"The email '{email}' is already registered.")


# --- Business rule violations -----------------------------------------------------


class InvalidFieldValue(BusinessRuleViolation):
    code = "INVALID_FIELD_VALUE"

    def __init__(self, field: str, reason: str) -> None:
        super().__init__(f"Invalid value for '{field}': {reason}")
        self.field = field
        self.reason = reason


class AssigneeNotFound(BusinessRuleViolation):
    code = "ASSIGNEE_NOT_FOUND"

    def __init__(self, email: str) -> None:
        super().__init__(f"There is no registered user with the email '{email}'.")


# --- Authentication ---------------------------------------------------------------


class InvalidCredentials(AuthenticationError):
    code = "INVALID_CREDENTIALS"

    def __init__(self) -> None:
        super().__init__("Incorrect email or password.")


class InvalidToken(AuthenticationError):
    code = "INVALID_TOKEN"

    def __init__(self) -> None:
        super().__init__("The access token is invalid or has expired.")
