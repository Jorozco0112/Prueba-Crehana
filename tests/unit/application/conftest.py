import pytest

from app.domain.task import Task
from app.domain.task_list import TaskList
from app.domain.user import User
from tests.factories import make_task, make_task_list, make_user
from tests.fakes import (
    FakePasswordHasher,
    FakeTokenService,
    FakeUnitOfWork,
    FixedClock,
    InMemoryNotifier,
    InMemoryTaskListRepository,
    InMemoryTaskRepository,
    InMemoryUserRepository,
)


@pytest.fixture
def events() -> list[str]:
    """Shared record of side effects, to check their order."""
    return []


@pytest.fixture
def users() -> InMemoryUserRepository:
    return InMemoryUserRepository()


@pytest.fixture
def task_lists() -> InMemoryTaskListRepository:
    return InMemoryTaskListRepository()


@pytest.fixture
def tasks() -> InMemoryTaskRepository:
    return InMemoryTaskRepository()


@pytest.fixture
def uow(events) -> FakeUnitOfWork:
    return FakeUnitOfWork(events)


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock()


@pytest.fixture
def hasher() -> FakePasswordHasher:
    return FakePasswordHasher()


@pytest.fixture
def tokens() -> FakeTokenService:
    return FakeTokenService()


@pytest.fixture
def notifier(events) -> InMemoryNotifier:
    return InMemoryNotifier(events)


@pytest.fixture
def owner(users) -> User:
    user = make_user(email="owner@example.com", full_name="Olivia Owner")
    users.add(user)
    return user


@pytest.fixture
def assignee(users) -> User:
    user = make_user(email="assignee@example.com", full_name="Adam Assignee")
    users.add(user)
    return user


@pytest.fixture
def stranger(users) -> User:
    user = make_user(email="stranger@example.com", full_name="Sam Stranger")
    users.add(user)
    return user


@pytest.fixture
def task_list(task_lists, owner) -> TaskList:
    task_list = make_task_list(owner_id=owner.id)
    task_lists.add(task_list)
    return task_list


@pytest.fixture
def task(tasks, task_list) -> Task:
    task = make_task(list_id=task_list.id)
    tasks.add(task)
    return task


@pytest.fixture
def assigned_task(tasks, task_list, assignee, clock) -> Task:
    task = make_task(list_id=task_list.id, title="Assigned task")
    task.assign_to(assignee.id, at=clock.now())
    tasks.add(task)
    return task
