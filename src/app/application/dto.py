"""Input and output objects of the use cases.

They carry data without rules, so they are immutable dataclasses; entities, which
protect invariants, are explicit classes (DEC-010).
"""

from dataclasses import dataclass
from typing import TypedDict

from app.domain.task import Task
from app.domain.value_objects import CompletionPercentage, Priority, TaskStatus


@dataclass(frozen=True, slots=True)
class PageRequest:
    limit: int = 10
    offset: int = 0


@dataclass(frozen=True, slots=True)
class Page[T]:
    items: list[T]
    total: int
    limit: int
    offset: int


@dataclass(frozen=True, slots=True)
class TaskFilters:
    status: TaskStatus | None = None
    priority: Priority | None = None


@dataclass(frozen=True, slots=True)
class TaskListing:
    """Tasks of a list (filtered and paginated) and the completion of the whole list."""

    page: Page[Task]
    completion: CompletionPercentage


@dataclass(frozen=True, slots=True)
class IssuedToken:
    access_token: str
    expires_in: int


class TaskListChanges(TypedDict, total=False):
    """Fields to change in a task list. A missing key means "leave it as is"."""

    name: str


class TaskChanges(TypedDict, total=False):
    """Fields to change in a task (DEC-022).

    A missing key means "leave it as is"; ``description: None`` clears it.
    """

    title: str
    description: str | None
    priority: Priority
