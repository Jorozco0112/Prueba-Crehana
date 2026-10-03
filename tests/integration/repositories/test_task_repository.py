from datetime import timedelta

import pytest

from app.application.dto import PageRequest, TaskFilters
from app.domain.exceptions import TaskNotFound
from app.domain.value_objects import CompletionPercentage, Priority, TaskStatus
from app.infrastructure.db.repositories import (
    SqlAlchemyTaskListRepository,
    SqlAlchemyTaskRepository,
    SqlAlchemyUserRepository,
)
from tests.factories import NOW, make_task, make_task_list, make_user

ALL = PageRequest(limit=100, offset=0)


@pytest.fixture
def owner(session):
    owner = make_user()
    SqlAlchemyUserRepository(session).add(owner)
    return owner


@pytest.fixture
def task_list(session, owner):
    task_list = make_task_list(owner_id=owner.id)
    SqlAlchemyTaskListRepository(session).add(task_list)
    session.flush()
    return task_list


@pytest.fixture
def tasks(session):
    return SqlAlchemyTaskRepository(session)


def test_round_trip_keeps_every_field(session, tasks, task_list, owner):
    task = make_task(
        list_id=task_list.id,
        title="Prepare demo",
        description="Slides and live run",
        priority=Priority.URGENT,
    )
    task.assign_to(owner.id, at=NOW + timedelta(minutes=1))
    task.change_status(TaskStatus.COMPLETED, at=NOW + timedelta(minutes=2))
    tasks.add(task)
    session.commit()
    session.expunge_all()

    stored = tasks.get(task.id)

    assert stored is not None
    assert (stored.title, stored.description) == ("Prepare demo", "Slides and live run")
    assert stored.priority is Priority.URGENT
    assert stored.status is TaskStatus.COMPLETED
    assert stored.assignee_id == owner.id
    assert stored.completed_at == NOW + timedelta(minutes=2)
    assert stored.created_at == NOW


def test_update_and_delete(session, tasks, task_list):
    task = make_task(list_id=task_list.id)
    tasks.add(task)
    session.commit()

    task.rename("Buy oat milk", at=NOW + timedelta(hours=1))
    tasks.update(task)
    session.commit()
    session.expunge_all()
    stored = tasks.get(task.id)
    assert stored is not None
    assert stored.title == "Buy oat milk"

    tasks.delete(task)
    session.commit()
    assert tasks.get(task.id) is None


def test_updating_a_missing_task_fails(tasks, task_list):
    with pytest.raises(TaskNotFound):
        tasks.update(make_task(list_id=task_list.id))


class TestListing:
    @pytest.fixture
    def populated(self, session, tasks, task_list):
        created = {
            "low_old": make_task(list_id=task_list.id, priority=Priority.LOW),
            "low_new": make_task(
                list_id=task_list.id,
                priority=Priority.LOW,
                now=NOW + timedelta(hours=1),
            ),
            "urgent": make_task(list_id=task_list.id, priority=Priority.URGENT),
            "high_done": make_task(list_id=task_list.id, priority=Priority.HIGH),
        }
        created["high_done"].change_status(TaskStatus.COMPLETED, at=NOW)
        for task in created.values():
            tasks.add(task)
        session.commit()
        return created

    def test_orders_by_priority_then_newest(self, tasks, task_list, populated):
        page = tasks.list_by_list(task_list.id, TaskFilters(), ALL)

        assert [task.id for task in page.items] == [
            populated[key].id for key in ("urgent", "high_done", "low_new", "low_old")
        ]

    def test_filters_by_status_and_priority(self, tasks, task_list, populated):
        by_status = tasks.list_by_list(
            task_list.id, TaskFilters(status=TaskStatus.COMPLETED), ALL
        )
        by_priority = tasks.list_by_list(
            task_list.id, TaskFilters(priority=Priority.LOW), ALL
        )

        assert [task.id for task in by_status.items] == [populated["high_done"].id]
        assert by_priority.total == 2

    def test_total_counts_matches_beyond_the_current_page(
        self, tasks, task_list, populated
    ):
        page = tasks.list_by_list(task_list.id, TaskFilters(), PageRequest(1, 1))

        assert [task.id for task in page.items] == [populated["high_done"].id]
        assert page.total == 4

    def test_completion_counts_the_whole_list(self, tasks, task_list, populated):
        assert tasks.completion_of(task_list.id) == CompletionPercentage(1, 4)

    def test_completion_of_an_empty_list(self, session, tasks, owner):
        empty = make_task_list(owner_id=owner.id, name="Empty")
        SqlAlchemyTaskListRepository(session).add(empty)
        session.flush()

        assert tasks.completion_of(empty.id) == CompletionPercentage(0, 0)

    def test_lists_tasks_by_assignee(self, session, tasks, task_list, owner, populated):
        task = populated["low_old"]
        task.assign_to(owner.id, at=NOW)
        tasks.update(task)
        session.commit()

        page = tasks.list_by_assignee(owner.id, ALL)

        assert [item.id for item in page.items] == [task.id]
