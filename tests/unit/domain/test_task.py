from datetime import timedelta
from uuid import uuid7

import pytest

from app.domain.exceptions import InvalidFieldValue
from app.domain.task import Task
from app.domain.task_list import TaskList
from app.domain.value_objects import Priority, TaskStatus
from tests.factories import NOW, make_task

LATER = NOW + timedelta(hours=1)
EVEN_LATER = NOW + timedelta(hours=2)


@pytest.fixture
def task() -> Task:
    return make_task(list_id=uuid7())


class TestCreation:
    def test_new_tasks_are_pending_and_unassigned(self, task):
        assert task.status == TaskStatus.PENDING
        assert task.assignee_id is None
        assert task.completed_at is None
        assert task.created_at == task.updated_at == NOW

    def test_title_and_description_are_cleaned(self):
        task = make_task(list_id=uuid7(), title="  Buy milk ", description="   ")

        assert task.title == "Buy milk"
        assert task.description is None

    def test_rejects_a_blank_title(self):
        with pytest.raises(InvalidFieldValue) as error:
            make_task(list_id=uuid7(), title="   ")

        assert error.value.field == "title"

    def test_rejects_a_title_over_200_characters(self):
        with pytest.raises(InvalidFieldValue, match="at most 200"):
            make_task(list_id=uuid7(), title="x" * 201)

    def test_rejects_a_description_over_2000_characters(self):
        with pytest.raises(InvalidFieldValue, match="at most 2000"):
            make_task(list_id=uuid7(), description="x" * 2001)


class TestChangeStatus:
    def test_completing_records_when_it_happened(self, task):
        task.change_status(TaskStatus.COMPLETED, at=LATER)

        assert task.status == TaskStatus.COMPLETED
        assert task.completed_at == LATER
        assert task.updated_at == LATER

    def test_leaving_completed_clears_the_completion_date(self, task):
        task.change_status(TaskStatus.COMPLETED, at=LATER)

        task.change_status(TaskStatus.PENDING, at=EVEN_LATER)

        assert task.status == TaskStatus.PENDING
        assert task.completed_at is None
        assert task.updated_at == EVEN_LATER

    def test_repeating_the_current_status_changes_nothing(self, task):
        task.change_status(TaskStatus.COMPLETED, at=LATER)

        task.change_status(TaskStatus.COMPLETED, at=EVEN_LATER)

        assert task.completed_at == LATER
        assert task.updated_at == LATER

    @pytest.mark.parametrize("origin", list(TaskStatus))
    @pytest.mark.parametrize("target", list(TaskStatus))
    def test_any_transition_is_allowed(self, task, origin, target):
        task.change_status(origin, at=LATER)

        task.change_status(target, at=EVEN_LATER)

        assert task.status == target
        assert (task.completed_at is not None) == (target == TaskStatus.COMPLETED)


class TestEditing:
    def test_rename(self, task):
        task.rename("  Buy oat milk ", at=LATER)

        assert task.title == "Buy oat milk"
        assert task.updated_at == LATER

    def test_rename_validates_the_new_title(self, task):
        with pytest.raises(InvalidFieldValue):
            task.rename("", at=LATER)

    def test_describe_sets_and_clears_the_description(self, task):
        task.describe("Two liters", at=LATER)
        assert task.description == "Two liters"

        task.describe(None, at=EVEN_LATER)
        assert task.description is None
        assert task.updated_at == EVEN_LATER

    def test_prioritize(self, task):
        task.prioritize(Priority.URGENT, at=LATER)

        assert task.priority == Priority.URGENT
        assert task.updated_at == LATER


class TestAssignment:
    def test_assigning_a_user(self, task):
        user_id = uuid7()

        changed = task.assign_to(user_id, at=LATER)

        assert changed is True
        assert task.assignee_id == user_id
        assert task.is_assigned_to(user_id)
        assert task.updated_at == LATER

    def test_assigning_the_same_user_again_changes_nothing(self, task):
        user_id = uuid7()
        task.assign_to(user_id, at=LATER)

        changed = task.assign_to(user_id, at=EVEN_LATER)

        assert changed is False
        assert task.updated_at == LATER

    def test_unassign(self, task):
        task.assign_to(uuid7(), at=LATER)

        task.unassign(at=EVEN_LATER)

        assert task.assignee_id is None
        assert task.updated_at == EVEN_LATER

    def test_unassigning_an_unassigned_task_changes_nothing(self, task):
        task.unassign(at=LATER)

        assert task.updated_at == NOW


class TestIdentity:
    def test_tasks_with_the_same_id_are_equal_even_with_different_data(self, task):
        same_task = Task(
            id=task.id,
            list_id=task.list_id,
            title="Another title",
            description=None,
            priority=Priority.LOW,
            status=TaskStatus.COMPLETED,
            assignee_id=None,
            created_at=NOW,
            updated_at=NOW,
            completed_at=NOW,
        )

        assert same_task == task
        assert hash(same_task) == hash(task)
        assert repr(task) == f"Task(id={task.id})"

    def test_tasks_with_different_ids_are_different(self):
        list_id = uuid7()

        assert make_task(list_id=list_id) != make_task(list_id=list_id)

    def test_an_entity_is_never_equal_to_another_type(self, task):
        task_list = TaskList(
            id=task.id, owner_id=uuid7(), name="Same ID", created_at=NOW, updated_at=NOW
        )

        assert task != task_list
        assert task != task.id
