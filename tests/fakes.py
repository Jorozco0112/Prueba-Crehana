"""In-memory implementations of the ports, used by the use case tests (DEC-037).

Repositories store copies, so a use case that forgets to call ``update()`` is caught
just like it would be against the real database.
"""

from copy import deepcopy
from datetime import datetime, timedelta
from uuid import UUID

from app.application.dto import IssuedToken, Page, PageRequest, TaskFilters
from app.application.ports import (
    Clock,
    PasswordHasher,
    TaskAssignmentNotifier,
    TaskListRepository,
    TaskRepository,
    TokenService,
    UnitOfWork,
    UserRepository,
)
from app.domain.exceptions import EmailAlreadyRegistered, InvalidToken
from app.domain.task import Task
from app.domain.task_list import TaskList
from app.domain.user import User
from app.domain.value_objects import CompletionPercentage, Email, TaskStatus
from tests.factories import NOW


def _paginate[T](items: list[T], page: PageRequest) -> Page[T]:
    return Page(
        items=items[page.offset : page.offset + page.limit],
        total=len(items),
        limit=page.limit,
        offset=page.offset,
    )


def _task_order(task: Task) -> tuple[int, datetime, UUID]:
    return (task.priority.rank, task.created_at, task.id)


class InMemoryUserRepository(UserRepository):
    def __init__(self) -> None:
        self.users: dict[UUID, User] = {}

    def add(self, user: User) -> None:
        if any(stored.email == user.email for stored in self.users.values()):
            raise EmailAlreadyRegistered(user.email.value)
        self.users[user.id] = deepcopy(user)

    def get(self, user_id: UUID) -> User | None:
        user = self.users.get(user_id)
        return deepcopy(user) if user is not None else None

    def get_by_email(self, email: Email) -> User | None:
        for user in self.users.values():
            if user.email == email:
                return deepcopy(user)
        return None


class InMemoryTaskListRepository(TaskListRepository):
    def __init__(self) -> None:
        self.task_lists: dict[UUID, TaskList] = {}

    def add(self, task_list: TaskList) -> None:
        self.task_lists[task_list.id] = deepcopy(task_list)

    def get(self, list_id: UUID) -> TaskList | None:
        task_list = self.task_lists.get(list_id)
        return deepcopy(task_list) if task_list is not None else None

    def update(self, task_list: TaskList) -> None:
        self.task_lists[task_list.id] = deepcopy(task_list)

    def delete(self, task_list: TaskList) -> None:
        del self.task_lists[task_list.id]

    def list_by_owner(self, owner_id: UUID, page: PageRequest) -> Page[TaskList]:
        owned = [
            deepcopy(task_list)
            for task_list in self.task_lists.values()
            if task_list.owner_id == owner_id
        ]
        owned.sort(key=lambda item: (item.created_at, item.id), reverse=True)
        return _paginate(owned, page)


class InMemoryTaskRepository(TaskRepository):
    def __init__(self) -> None:
        self.tasks: dict[UUID, Task] = {}

    def add(self, task: Task) -> None:
        self.tasks[task.id] = deepcopy(task)

    def get(self, task_id: UUID) -> Task | None:
        task = self.tasks.get(task_id)
        return deepcopy(task) if task is not None else None

    def update(self, task: Task) -> None:
        self.tasks[task.id] = deepcopy(task)

    def delete(self, task: Task) -> None:
        del self.tasks[task.id]

    def list_by_list(
        self, list_id: UUID, filters: TaskFilters, page: PageRequest
    ) -> Page[Task]:
        matching = [
            deepcopy(task)
            for task in self.tasks.values()
            if task.list_id == list_id
            and (filters.status is None or task.status == filters.status)
            and (filters.priority is None or task.priority == filters.priority)
        ]
        matching.sort(key=_task_order, reverse=True)
        return _paginate(matching, page)

    def list_by_assignee(self, assignee_id: UUID, page: PageRequest) -> Page[Task]:
        assigned = [
            deepcopy(task)
            for task in self.tasks.values()
            if task.assignee_id == assignee_id
        ]
        assigned.sort(key=_task_order, reverse=True)
        return _paginate(assigned, page)

    def completion_of(self, list_id: UUID) -> CompletionPercentage:
        in_list = [task for task in self.tasks.values() if task.list_id == list_id]
        completed = sum(task.status == TaskStatus.COMPLETED for task in in_list)
        return CompletionPercentage.from_counts(completed=completed, total=len(in_list))


class FakeUnitOfWork(UnitOfWork):
    def __init__(self, events: list[str] | None = None) -> None:
        self.commits = 0
        self.rollbacks = 0
        self._events = events if events is not None else []

    @property
    def committed(self) -> bool:
        return self.commits > 0

    def commit(self) -> None:
        self.commits += 1
        self._events.append("commit")

    def rollback(self) -> None:
        self.rollbacks += 1


class FixedClock(Clock):
    def __init__(self, now: datetime = NOW) -> None:
        self.current = now

    def now(self) -> datetime:
        return self.current

    def advance(self, **delta: float) -> datetime:
        self.current += timedelta(**delta)
        return self.current


class FakePasswordHasher(PasswordHasher):
    """Readable "hashes" and a record of every check, including dummy ones."""

    def __init__(self) -> None:
        self.verified: list[str | None] = []

    def hash(self, password: str) -> str:
        return f"hashed::{password}"

    def verify(self, password: str, password_hash: str | None) -> bool:
        self.verified.append(password_hash)
        return password_hash is not None and password_hash == self.hash(password)


class FakeTokenService(TokenService):
    """Tokens look like ``token::<user id>::<expiry timestamp>``."""

    LIFETIME = timedelta(minutes=30)

    def issue(self, user_id: UUID, *, now: datetime) -> IssuedToken:
        expires_at = int((now + self.LIFETIME).timestamp())
        return IssuedToken(
            access_token=f"token::{user_id}::{expires_at}",
            expires_in=int(self.LIFETIME.total_seconds()),
        )

    def decode(self, token: str, *, now: datetime) -> UUID:
        try:
            prefix, user_id, expires_at = token.split("::")
            if prefix != "token" or int(expires_at) <= now.timestamp():
                raise ValueError(token)
            return UUID(user_id)
        except ValueError as error:
            raise InvalidToken() from error


class InMemoryNotifier(TaskAssignmentNotifier):
    def __init__(self, events: list[str] | None = None, *, fail: bool = False) -> None:
        self.sent: list[tuple[Task, User]] = []
        self.fail = fail
        self._events = events if events is not None else []

    def notify_assigned(self, task: Task, assignee: User) -> None:
        if self.fail:
            raise RuntimeError("SMTP server unavailable")
        self.sent.append((deepcopy(task), deepcopy(assignee)))
        self._events.append("notify")
