"""SQLAlchemy implementations of the repository ports.

Repositories never commit: they only stage changes in the session, and the use case
decides when the operation is done (DEC-017).
"""

from collections.abc import Callable
from uuid import UUID

from psycopg.errors import UniqueViolation
from sqlalchemy import Select, delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.application.dto import Page, PageRequest, TaskFilters
from app.application.ports import TaskListRepository, TaskRepository, UserRepository
from app.domain.exceptions import EmailAlreadyRegistered, TaskListNotFound, TaskNotFound
from app.domain.task import Task
from app.domain.task_list import TaskList
from app.domain.user import User
from app.domain.value_objects import CompletionPercentage, Email, TaskStatus
from app.infrastructure.db.mappers import (
    copy_task,
    copy_task_list,
    task_list_to_entity,
    task_list_to_model,
    task_to_entity,
    task_to_model,
    user_to_entity,
    user_to_model,
)
from app.infrastructure.db.models import (
    USERS_EMAIL_UNIQUE_CONSTRAINT,
    TaskListModel,
    TaskModel,
    UserModel,
)


class SqlAlchemyUserRepository(UserRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, user: User) -> None:
        self._session.add(user_to_model(user))
        try:
            # Flush now so a duplicate email is detected inside the use case.
            self._session.flush()
        except IntegrityError as error:
            if _violates(error, USERS_EMAIL_UNIQUE_CONSTRAINT):
                raise EmailAlreadyRegistered(user.email.value) from error
            raise

    def get(self, user_id: UUID) -> User | None:
        model = self._session.get(UserModel, user_id)
        return user_to_entity(model) if model is not None else None

    def get_by_email(self, email: Email) -> User | None:
        model = self._session.scalar(
            select(UserModel).where(UserModel.email == email.value)
        )
        return user_to_entity(model) if model is not None else None


class SqlAlchemyTaskListRepository(TaskListRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, task_list: TaskList) -> None:
        self._session.add(task_list_to_model(task_list))

    def get(self, list_id: UUID) -> TaskList | None:
        model = self._session.get(TaskListModel, list_id)
        return task_list_to_entity(model) if model is not None else None

    def update(self, task_list: TaskList) -> None:
        model = self._session.get(TaskListModel, task_list.id)
        if model is None:
            raise TaskListNotFound(task_list.id)
        copy_task_list(task_list, model)

    def delete(self, task_list: TaskList) -> None:
        # The foreign key's ON DELETE CASCADE removes the tasks.
        self._session.execute(
            delete(TaskListModel).where(TaskListModel.id == task_list.id)
        )

    def list_by_owner(self, owner_id: UUID, page: PageRequest) -> Page[TaskList]:
        query = select(TaskListModel).where(TaskListModel.owner_id == owner_id)
        ordered = query.order_by(
            TaskListModel.created_at.desc(), TaskListModel.id.desc()
        )
        return _paginate(self._session, query, ordered, page, task_list_to_entity)


class SqlAlchemyTaskRepository(TaskRepository):
    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, task: Task) -> None:
        self._session.add(task_to_model(task))

    def get(self, task_id: UUID) -> Task | None:
        model = self._session.get(TaskModel, task_id)
        return task_to_entity(model) if model is not None else None

    def update(self, task: Task) -> None:
        model = self._session.get(TaskModel, task.id)
        if model is None:
            raise TaskNotFound(task.id)
        copy_task(task, model)

    def delete(self, task: Task) -> None:
        self._session.execute(delete(TaskModel).where(TaskModel.id == task.id))

    def list_by_list(
        self, list_id: UUID, filters: TaskFilters, page: PageRequest
    ) -> Page[Task]:
        query = select(TaskModel).where(TaskModel.list_id == list_id)
        if filters.status is not None:
            query = query.where(TaskModel.status == filters.status.value)
        if filters.priority is not None:
            query = query.where(TaskModel.priority == filters.priority.rank)
        return _paginate(
            self._session, query, _in_task_order(query), page, task_to_entity
        )

    def list_by_assignee(self, assignee_id: UUID, page: PageRequest) -> Page[Task]:
        query = select(TaskModel).where(TaskModel.assignee_id == assignee_id)
        return _paginate(
            self._session, query, _in_task_order(query), page, task_to_entity
        )

    def completion_of(self, list_id: UUID) -> CompletionPercentage:
        # One aggregate query over the whole list, independent of filters and
        # pagination (DEC-008).
        completed, total = self._session.execute(
            select(
                func.count().filter(TaskModel.status == TaskStatus.COMPLETED.value),
                func.count(),
            ).where(TaskModel.list_id == list_id)
        ).one()
        return CompletionPercentage.from_counts(completed=completed, total=total)


def _in_task_order(query: Select[TaskModel]) -> Select[TaskModel]:
    """Most important first, then newest; the ID makes the order total (DEC-024)."""
    return query.order_by(
        TaskModel.priority.desc(), TaskModel.created_at.desc(), TaskModel.id.desc()
    )


def _paginate[M, E](
    session: Session,
    query: Select[M],
    ordered: Select[M],
    page: PageRequest,
    to_entity: Callable[[M], E],
) -> Page[E]:
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    models = session.scalars(ordered.limit(page.limit).offset(page.offset)).all()
    return Page(
        items=[to_entity(model) for model in models],
        total=total,
        limit=page.limit,
        offset=page.offset,
    )


def _violates(error: IntegrityError, constraint: str) -> bool:
    cause = error.orig
    return (
        isinstance(cause, UniqueViolation) and cause.diag.constraint_name == constraint
    )
