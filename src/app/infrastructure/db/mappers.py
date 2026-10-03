"""Conversions between SQLAlchemy models and domain entities (DEC-016)."""

from app.domain.task import Task
from app.domain.task_list import TaskList
from app.domain.user import User
from app.domain.value_objects import Email, Priority, TaskStatus
from app.infrastructure.db.models import TaskListModel, TaskModel, UserModel


def user_to_entity(model: UserModel) -> User:
    return User(
        id=model.id,
        email=Email(model.email),
        full_name=model.full_name,
        password_hash=model.password_hash,
        created_at=model.created_at,
    )


def user_to_model(user: User) -> UserModel:
    return UserModel(
        id=user.id,
        email=user.email.value,
        full_name=user.full_name,
        password_hash=user.password_hash,
        created_at=user.created_at,
    )


def task_list_to_entity(model: TaskListModel) -> TaskList:
    return TaskList(
        id=model.id,
        owner_id=model.owner_id,
        name=model.name,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def task_list_to_model(task_list: TaskList) -> TaskListModel:
    model = TaskListModel(id=task_list.id, owner_id=task_list.owner_id)
    copy_task_list(task_list, model)
    return model


def copy_task_list(task_list: TaskList, model: TaskListModel) -> None:
    model.name = task_list.name
    model.created_at = task_list.created_at
    model.updated_at = task_list.updated_at


def task_to_entity(model: TaskModel) -> Task:
    return Task(
        id=model.id,
        list_id=model.list_id,
        title=model.title,
        description=model.description,
        priority=Priority.from_rank(model.priority),
        status=TaskStatus(model.status),
        assignee_id=model.assignee_id,
        created_at=model.created_at,
        updated_at=model.updated_at,
        completed_at=model.completed_at,
    )


def task_to_model(task: Task) -> TaskModel:
    model = TaskModel(id=task.id, list_id=task.list_id)
    copy_task(task, model)
    return model


def copy_task(task: Task, model: TaskModel) -> None:
    model.title = task.title
    model.description = task.description
    model.priority = task.priority.rank
    model.status = task.status.value
    model.assignee_id = task.assignee_id
    model.created_at = task.created_at
    model.updated_at = task.updated_at
    model.completed_at = task.completed_at
