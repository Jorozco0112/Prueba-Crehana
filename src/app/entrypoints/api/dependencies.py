"""Composition root: the only module that knows every layer (DEC-013).

Each provider builds a use case with its concrete adapters. Routes receive them through
``Depends``, and tests can replace any of them with ``app.dependency_overrides``.
"""

from collections.abc import Iterator
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Query
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.application.dto import PageRequest
from app.application.ports import (
    Clock,
    PasswordHasher,
    TaskAssignmentNotifier,
    TokenService,
)
from app.application.use_cases.auth.get_authenticated_user import GetAuthenticatedUser
from app.application.use_cases.auth.log_in import LogIn
from app.application.use_cases.auth.register_user import RegisterUser
from app.application.use_cases.task_lists.create_task_list import CreateTaskList
from app.application.use_cases.task_lists.delete_task_list import DeleteTaskList
from app.application.use_cases.task_lists.get_task_list import GetTaskList
from app.application.use_cases.task_lists.list_task_lists import ListTaskLists
from app.application.use_cases.task_lists.update_task_list import UpdateTaskList
from app.application.use_cases.tasks.assign_task import AssignTask
from app.application.use_cases.tasks.change_task_status import ChangeTaskStatus
from app.application.use_cases.tasks.create_task import CreateTask
from app.application.use_cases.tasks.delete_task import DeleteTask
from app.application.use_cases.tasks.get_task import GetTask
from app.application.use_cases.tasks.list_assigned_tasks import ListAssignedTasks
from app.application.use_cases.tasks.list_tasks import ListTasks
from app.application.use_cases.tasks.unassign_task import UnassignTask
from app.application.use_cases.tasks.update_task import UpdateTask
from app.domain.user import User
from app.infrastructure.clock import SystemClock
from app.infrastructure.config import get_auth_settings
from app.infrastructure.db.repositories import (
    SqlAlchemyTaskListRepository,
    SqlAlchemyTaskRepository,
    SqlAlchemyUserRepository,
)
from app.infrastructure.db.session import get_session_factory
from app.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from app.infrastructure.notifications.logging_notifier import (
    LoggingTaskAssignmentNotifier,
)
from app.infrastructure.security.password_hasher import Argon2PasswordHasher
from app.infrastructure.security.token_service import JwtTokenService

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100

# --- Infrastructure ---------------------------------------------------------------


def get_session() -> Iterator[Session]:
    """One session per request, shared by every repository of that request."""
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


SessionDep = Annotated[Session, Depends(get_session)]


def get_clock() -> Clock:
    return SystemClock()


ClockDep = Annotated[Clock, Depends(get_clock)]


@lru_cache
def get_password_hasher() -> PasswordHasher:
    return Argon2PasswordHasher()


@lru_cache
def get_token_service() -> TokenService:
    settings = get_auth_settings()
    return JwtTokenService(
        secret_key=settings.jwt_secret_key.get_secret_value(),
        expire_minutes=settings.jwt_expire_minutes,
    )


def get_notifier() -> TaskAssignmentNotifier:
    return LoggingTaskAssignmentNotifier()


HasherDep = Annotated[PasswordHasher, Depends(get_password_hasher)]
TokensDep = Annotated[TokenService, Depends(get_token_service)]
NotifierDep = Annotated[TaskAssignmentNotifier, Depends(get_notifier)]

# --- Request context --------------------------------------------------------------

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: SessionDep,
    tokens: TokensDep,
    clock: ClockDep,
) -> User:
    use_case = GetAuthenticatedUser(SqlAlchemyUserRepository(session), tokens, clock)
    return use_case.execute(token)


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_page_request(
    limit: Annotated[int, Query(ge=1, le=MAX_PAGE_SIZE)] = DEFAULT_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> PageRequest:
    return PageRequest(limit=limit, offset=offset)


PageRequestDep = Annotated[PageRequest, Depends(get_page_request)]

# --- Use cases: authentication ----------------------------------------------------


def get_register_user(
    session: SessionDep, hasher: HasherDep, clock: ClockDep
) -> RegisterUser:
    return RegisterUser(
        users=SqlAlchemyUserRepository(session),
        hasher=hasher,
        uow=SqlAlchemyUnitOfWork(session),
        clock=clock,
    )


def get_log_in(
    session: SessionDep, hasher: HasherDep, tokens: TokensDep, clock: ClockDep
) -> LogIn:
    return LogIn(
        users=SqlAlchemyUserRepository(session),
        hasher=hasher,
        tokens=tokens,
        clock=clock,
    )


# --- Use cases: task lists --------------------------------------------------------


def get_create_task_list(session: SessionDep, clock: ClockDep) -> CreateTaskList:
    return CreateTaskList(
        task_lists=SqlAlchemyTaskListRepository(session),
        uow=SqlAlchemyUnitOfWork(session),
        clock=clock,
    )


def get_get_task_list(session: SessionDep) -> GetTaskList:
    return GetTaskList(task_lists=SqlAlchemyTaskListRepository(session))


def get_list_task_lists(session: SessionDep) -> ListTaskLists:
    return ListTaskLists(task_lists=SqlAlchemyTaskListRepository(session))


def get_update_task_list(session: SessionDep, clock: ClockDep) -> UpdateTaskList:
    return UpdateTaskList(
        task_lists=SqlAlchemyTaskListRepository(session),
        uow=SqlAlchemyUnitOfWork(session),
        clock=clock,
    )


def get_delete_task_list(session: SessionDep) -> DeleteTaskList:
    return DeleteTaskList(
        task_lists=SqlAlchemyTaskListRepository(session),
        uow=SqlAlchemyUnitOfWork(session),
    )


# --- Use cases: tasks -------------------------------------------------------------


def get_create_task(session: SessionDep, clock: ClockDep) -> CreateTask:
    return CreateTask(
        tasks=SqlAlchemyTaskRepository(session),
        task_lists=SqlAlchemyTaskListRepository(session),
        uow=SqlAlchemyUnitOfWork(session),
        clock=clock,
    )


def get_get_task(session: SessionDep) -> GetTask:
    return GetTask(
        tasks=SqlAlchemyTaskRepository(session),
        task_lists=SqlAlchemyTaskListRepository(session),
    )


def get_list_tasks(session: SessionDep) -> ListTasks:
    return ListTasks(
        tasks=SqlAlchemyTaskRepository(session),
        task_lists=SqlAlchemyTaskListRepository(session),
    )


def get_update_task(session: SessionDep, clock: ClockDep) -> UpdateTask:
    return UpdateTask(
        tasks=SqlAlchemyTaskRepository(session),
        task_lists=SqlAlchemyTaskListRepository(session),
        uow=SqlAlchemyUnitOfWork(session),
        clock=clock,
    )


def get_delete_task(session: SessionDep) -> DeleteTask:
    return DeleteTask(
        tasks=SqlAlchemyTaskRepository(session),
        task_lists=SqlAlchemyTaskListRepository(session),
        uow=SqlAlchemyUnitOfWork(session),
    )


def get_change_task_status(session: SessionDep, clock: ClockDep) -> ChangeTaskStatus:
    return ChangeTaskStatus(
        tasks=SqlAlchemyTaskRepository(session),
        task_lists=SqlAlchemyTaskListRepository(session),
        uow=SqlAlchemyUnitOfWork(session),
        clock=clock,
    )


def get_assign_task(
    session: SessionDep, notifier: NotifierDep, clock: ClockDep
) -> AssignTask:
    return AssignTask(
        tasks=SqlAlchemyTaskRepository(session),
        task_lists=SqlAlchemyTaskListRepository(session),
        users=SqlAlchemyUserRepository(session),
        notifier=notifier,
        uow=SqlAlchemyUnitOfWork(session),
        clock=clock,
    )


def get_unassign_task(session: SessionDep, clock: ClockDep) -> UnassignTask:
    return UnassignTask(
        tasks=SqlAlchemyTaskRepository(session),
        task_lists=SqlAlchemyTaskListRepository(session),
        uow=SqlAlchemyUnitOfWork(session),
        clock=clock,
    )


def get_list_assigned_tasks(session: SessionDep) -> ListAssignedTasks:
    return ListAssignedTasks(tasks=SqlAlchemyTaskRepository(session))
