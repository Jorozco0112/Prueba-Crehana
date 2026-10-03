from datetime import timedelta
from uuid import uuid7

import pytest

from app.application.dto import PageRequest, TaskFilters
from app.application.use_cases.tasks.change_task_status import ChangeTaskStatus
from app.application.use_cases.tasks.create_task import CreateTask
from app.application.use_cases.tasks.delete_task import DeleteTask
from app.application.use_cases.tasks.get_task import GetTask
from app.application.use_cases.tasks.list_assigned_tasks import ListAssignedTasks
from app.application.use_cases.tasks.list_tasks import ListTasks
from app.application.use_cases.tasks.unassign_task import UnassignTask
from app.application.use_cases.tasks.update_task import UpdateTask
from app.domain.exceptions import NotTaskOwner, TaskListNotFound, TaskNotFound
from app.domain.value_objects import Priority, TaskStatus
from tests.factories import NOW, make_task, make_task_list

ALL = PageRequest(limit=100, offset=0)


class TestCreateTask:
    @pytest.fixture
    def create(self, tasks, task_lists, uow, clock) -> CreateTask:
        return CreateTask(tasks=tasks, task_lists=task_lists, uow=uow, clock=clock)

    def test_creates_a_pending_task_in_the_list(self, create, tasks, task_list, owner):
        task = create.execute(
            list_id=task_list.id,
            user_id=owner.id,
            title="Buy milk",
            priority=Priority.HIGH,
        )

        assert tasks.get(task.id) == task
        assert task.status == TaskStatus.PENDING
        assert task.priority == Priority.HIGH

    def test_cannot_create_in_another_users_list(self, create, task_list, stranger):
        with pytest.raises(TaskListNotFound):
            create.execute(list_id=task_list.id, user_id=stranger.id, title="Hack")

    def test_cannot_create_in_a_missing_list(self, create, owner):
        with pytest.raises(TaskListNotFound):
            create.execute(list_id=uuid7(), user_id=owner.id, title="Lost")


class TestGetTask:
    @pytest.fixture
    def get(self, tasks, task_lists) -> GetTask:
        return GetTask(tasks=tasks, task_lists=task_lists)

    def test_owner_and_assignee_can_see_it(self, get, assigned_task, owner, assignee):
        assert get.execute(task_id=assigned_task.id, user_id=owner.id) == assigned_task
        assert (
            get.execute(task_id=assigned_task.id, user_id=assignee.id) == assigned_task
        )

    def test_anyone_else_gets_not_found(self, get, assigned_task, stranger):
        with pytest.raises(TaskNotFound):
            get.execute(task_id=assigned_task.id, user_id=stranger.id)

    def test_a_missing_task_is_not_found(self, get, owner):
        with pytest.raises(TaskNotFound):
            get.execute(task_id=uuid7(), user_id=owner.id)

    def test_a_task_whose_list_disappeared_is_not_found(
        self, get, tasks, task_lists, task, task_list, owner
    ):
        task_lists.delete(task_list)

        with pytest.raises(TaskNotFound):
            get.execute(task_id=task.id, user_id=owner.id)


class TestUpdateTask:
    @pytest.fixture
    def update(self, tasks, task_lists, uow, clock) -> UpdateTask:
        return UpdateTask(tasks=tasks, task_lists=task_lists, uow=uow, clock=clock)

    def test_owner_edits_only_the_fields_sent(self, update, tasks, uow, task, owner):
        update.execute(
            task_id=task.id,
            user_id=owner.id,
            changes={"title": "Buy oat milk", "priority": Priority.URGENT},
        )

        stored = tasks.get(task.id)
        assert stored is not None
        assert stored.title == "Buy oat milk"
        assert stored.priority == Priority.URGENT
        assert stored.description == task.description
        assert uow.committed

    def test_description_none_clears_it(self, update, tasks, task_list, owner):
        task = make_task(list_id=task_list.id, description="Two liters")
        tasks.add(task)

        update.execute(task_id=task.id, user_id=owner.id, changes={"description": None})

        stored = tasks.get(task.id)
        assert stored is not None
        assert stored.description is None

    def test_no_changes_means_no_commit(self, update, uow, task, owner):
        update.execute(task_id=task.id, user_id=owner.id, changes={})

        assert not uow.committed

    def test_the_assignee_is_forbidden(self, update, assigned_task, assignee):
        with pytest.raises(NotTaskOwner):
            update.execute(
                task_id=assigned_task.id, user_id=assignee.id, changes={"title": "x"}
            )

    def test_anyone_else_gets_not_found(self, update, task, stranger):
        with pytest.raises(TaskNotFound):
            update.execute(task_id=task.id, user_id=stranger.id, changes={"title": "x"})


class TestDeleteTask:
    @pytest.fixture
    def delete(self, tasks, task_lists, uow) -> DeleteTask:
        return DeleteTask(tasks=tasks, task_lists=task_lists, uow=uow)

    def test_owner_deletes_it(self, delete, tasks, uow, task, owner):
        delete.execute(task_id=task.id, user_id=owner.id)

        assert tasks.get(task.id) is None
        assert uow.committed

    def test_the_assignee_is_forbidden(self, delete, tasks, assigned_task, assignee):
        with pytest.raises(NotTaskOwner):
            delete.execute(task_id=assigned_task.id, user_id=assignee.id)

        assert tasks.get(assigned_task.id) is not None


class TestChangeTaskStatus:
    @pytest.fixture
    def change(self, tasks, task_lists, uow, clock) -> ChangeTaskStatus:
        return ChangeTaskStatus(
            tasks=tasks, task_lists=task_lists, uow=uow, clock=clock
        )

    def test_completing_uses_the_clock_time(
        self, change, tasks, uow, clock, task, owner
    ):
        completed_at = clock.advance(hours=2)

        change.execute(task_id=task.id, user_id=owner.id, status=TaskStatus.COMPLETED)

        stored = tasks.get(task.id)
        assert stored is not None
        assert stored.status == TaskStatus.COMPLETED
        assert stored.completed_at == completed_at
        assert uow.committed

    def test_the_assignee_can_change_it(self, change, tasks, assigned_task, assignee):
        change.execute(
            task_id=assigned_task.id, user_id=assignee.id, status=TaskStatus.IN_PROGRESS
        )

        stored = tasks.get(assigned_task.id)
        assert stored is not None
        assert stored.status == TaskStatus.IN_PROGRESS

    def test_repeating_the_status_does_not_commit(self, change, uow, task, owner):
        change.execute(task_id=task.id, user_id=owner.id, status=TaskStatus.PENDING)

        assert not uow.committed

    def test_anyone_else_gets_not_found(self, change, task, stranger):
        with pytest.raises(TaskNotFound):
            change.execute(
                task_id=task.id, user_id=stranger.id, status=TaskStatus.COMPLETED
            )


class TestListTasks:
    @pytest.fixture
    def list_tasks(self, tasks, task_lists) -> ListTasks:
        return ListTasks(tasks=tasks, task_lists=task_lists)

    @pytest.fixture
    def populated(self, tasks, task_list):
        """Five tasks: two completed (one HIGH), one HIGH pending, two LOW pending."""
        created = {
            "low_old": make_task(list_id=task_list.id, priority=Priority.LOW, now=NOW),
            "low_new": make_task(
                list_id=task_list.id, priority=Priority.LOW, now=NOW + timedelta(1)
            ),
            "high_pending": make_task(list_id=task_list.id, priority=Priority.HIGH),
            "high_done": make_task(list_id=task_list.id, priority=Priority.HIGH),
            "medium_done": make_task(list_id=task_list.id),
        }
        for key in ("high_done", "medium_done"):
            created[key].change_status(TaskStatus.COMPLETED, at=NOW)
        for task in created.values():
            tasks.add(task)
        return created

    def test_completion_covers_the_whole_list_whatever_the_filter(
        self, list_tasks, populated, task_list, owner
    ):
        listing = list_tasks.execute(
            list_id=task_list.id,
            user_id=owner.id,
            filters=TaskFilters(status=TaskStatus.COMPLETED),
            page=ALL,
        )

        assert listing.page.total == 2
        assert (listing.completion.completed, listing.completion.total) == (2, 5)

    def test_filters_combine_status_and_priority(
        self, list_tasks, populated, task_list, owner
    ):
        listing = list_tasks.execute(
            list_id=task_list.id,
            user_id=owner.id,
            filters=TaskFilters(status=TaskStatus.PENDING, priority=Priority.HIGH),
            page=ALL,
        )

        assert listing.page.items == [populated["high_pending"]]

    def test_orders_by_priority_then_newest(
        self, list_tasks, populated, task_list, owner
    ):
        listing = list_tasks.execute(
            list_id=task_list.id,
            user_id=owner.id,
            filters=TaskFilters(priority=Priority.LOW),
            page=ALL,
        )

        assert listing.page.items == [populated["low_new"], populated["low_old"]]

    def test_another_users_list_is_not_found(self, list_tasks, task_list, stranger):
        with pytest.raises(TaskListNotFound):
            list_tasks.execute(
                list_id=task_list.id,
                user_id=stranger.id,
                filters=TaskFilters(),
                page=ALL,
            )


class TestListAssignedTasks:
    def test_returns_tasks_assigned_to_the_user_across_lists(
        self, tasks, task_lists, assigned_task, assignee, owner, clock
    ):
        other_list = make_task_list(owner_id=owner.id, name="Work")
        task_lists.add(other_list)
        other_task = make_task(list_id=other_list.id, priority=Priority.URGENT)
        other_task.assign_to(assignee.id, at=clock.now())
        tasks.add(other_task)
        tasks.add(make_task(list_id=other_list.id, title="Not assigned"))

        page = ListAssignedTasks(tasks=tasks).execute(user_id=assignee.id, page=ALL)

        assert page.items == [other_task, assigned_task]


class TestUnassignTask:
    @pytest.fixture
    def unassign(self, tasks, task_lists, uow, clock) -> UnassignTask:
        return UnassignTask(tasks=tasks, task_lists=task_lists, uow=uow, clock=clock)

    def test_owner_removes_the_assignee(
        self, unassign, tasks, uow, assigned_task, owner
    ):
        unassign.execute(task_id=assigned_task.id, user_id=owner.id)

        stored = tasks.get(assigned_task.id)
        assert stored is not None
        assert stored.assignee_id is None
        assert uow.committed

    def test_unassigning_an_unassigned_task_does_not_commit(
        self, unassign, uow, task, owner
    ):
        unassign.execute(task_id=task.id, user_id=owner.id)

        assert not uow.committed

    def test_the_assignee_is_forbidden(self, unassign, assigned_task, assignee):
        with pytest.raises(NotTaskOwner):
            unassign.execute(task_id=assigned_task.id, user_id=assignee.id)
