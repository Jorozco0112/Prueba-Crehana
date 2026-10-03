"""Ports: what the use cases need from the outside world (DEC-011).

They live in the application layer because only the use cases depend on them. The
implementations (adapters) live in ``app.infrastructure``.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from app.application.dto import IssuedToken, Page, PageRequest, TaskFilters
from app.domain.task import Task
from app.domain.task_list import TaskList
from app.domain.user import User
from app.domain.value_objects import CompletionPercentage, Email

# --- Repositories -----------------------------------------------------------------


class UserRepository(ABC):
    @abstractmethod
    def add(self, user: User) -> None:
        """Store a new user. Raises ``EmailAlreadyRegistered`` on a duplicate email."""

    @abstractmethod
    def get(self, user_id: UUID) -> User | None:
        """Return the user, or ``None`` if it does not exist."""

    @abstractmethod
    def get_by_email(self, email: Email) -> User | None:
        """Return the user registered with ``email``, or ``None``."""


class TaskListRepository(ABC):
    @abstractmethod
    def add(self, task_list: TaskList) -> None:
        """Store a new task list."""

    @abstractmethod
    def get(self, list_id: UUID) -> TaskList | None:
        """Return the task list, or ``None`` if it does not exist."""

    @abstractmethod
    def update(self, task_list: TaskList) -> None:
        """Persist the changes made to an existing task list."""

    @abstractmethod
    def delete(self, task_list: TaskList) -> None:
        """Delete the task list together with its tasks."""

    @abstractmethod
    def list_by_owner(self, owner_id: UUID, page: PageRequest) -> Page[TaskList]:
        """Lists owned by ``owner_id``, newest first."""


class TaskRepository(ABC):
    @abstractmethod
    def add(self, task: Task) -> None:
        """Store a new task."""

    @abstractmethod
    def get(self, task_id: UUID) -> Task | None:
        """Return the task, or ``None`` if it does not exist."""

    @abstractmethod
    def update(self, task: Task) -> None:
        """Persist the changes made to an existing task."""

    @abstractmethod
    def delete(self, task: Task) -> None:
        """Delete the task."""

    @abstractmethod
    def list_by_list(
        self, list_id: UUID, filters: TaskFilters, page: PageRequest
    ) -> Page[Task]:
        """Tasks of a list matching ``filters``, in the order defined by DEC-024."""

    @abstractmethod
    def list_by_assignee(self, assignee_id: UUID, page: PageRequest) -> Page[Task]:
        """Tasks assigned to ``assignee_id``, in the order defined by DEC-024."""

    @abstractmethod
    def completion_of(self, list_id: UUID) -> CompletionPercentage:
        """Completion of the whole list, regardless of any filter (DEC-008)."""


# --- Transactions -----------------------------------------------------------------


class UnitOfWork(ABC):
    """Lets each use case decide when its business operation is done (DEC-017)."""

    @abstractmethod
    def commit(self) -> None:
        """Make every pending change permanent."""

    @abstractmethod
    def rollback(self) -> None:
        """Discard every pending change."""


# --- External services ------------------------------------------------------------


class Clock(ABC):
    """Source of the current time; the domain never reads it by itself (DEC-038)."""

    @abstractmethod
    def now(self) -> datetime:
        """Current time as a timezone-aware UTC datetime."""


class PasswordHasher(ABC):
    @abstractmethod
    def hash(self, password: str) -> str:
        """Return a salted hash of ``password``."""

    @abstractmethod
    def verify(self, password: str, password_hash: str | None) -> bool:
        """Check ``password`` against ``password_hash``.

        When ``password_hash`` is ``None`` (unknown user) the check still runs against a
        dummy hash and returns ``False``, so response times do not reveal which emails
        are registered (DEC-031).
        """


class TokenService(ABC):
    @abstractmethod
    def issue(self, user_id: UUID, *, now: datetime) -> IssuedToken:
        """Create an access token for ``user_id``."""

    @abstractmethod
    def decode(self, token: str, *, now: datetime) -> UUID:
        """Return the user ID in ``token``; raise ``InvalidToken`` if it is invalid."""


class TaskAssignmentNotifier(ABC):
    """Named after the intent, not the channel: email today, anything tomorrow."""

    @abstractmethod
    def notify_assigned(self, task: Task, assignee: User) -> None:
        """Let ``assignee`` know that ``task`` was assigned to them."""
