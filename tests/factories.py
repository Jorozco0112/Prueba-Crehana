"""Small builders for test data (DEC-034)."""

from datetime import UTC, datetime
from uuid import UUID

from app.domain.task import Task
from app.domain.task_list import TaskList
from app.domain.user import User
from app.domain.value_objects import Email, Priority

NOW = datetime(2026, 1, 15, 12, 0, tzinfo=UTC)


def make_user(
    *,
    email: str = "ana@example.com",
    full_name: str = "Ana Torres",
    password_hash: str = "hashed::correct-horse",
    now: datetime = NOW,
) -> User:
    return User.register(
        email=Email(email), full_name=full_name, password_hash=password_hash, now=now
    )


def make_task_list(
    *, owner_id: UUID, name: str = "Groceries", now: datetime = NOW
) -> TaskList:
    return TaskList.create(owner_id=owner_id, name=name, now=now)


def make_task(
    *,
    list_id: UUID,
    title: str = "Buy milk",
    description: str | None = None,
    priority: Priority = Priority.MEDIUM,
    now: datetime = NOW,
) -> Task:
    return Task.create(
        list_id=list_id,
        title=title,
        description=description,
        priority=priority,
        now=now,
    )
