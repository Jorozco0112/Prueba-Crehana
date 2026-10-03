import logging

import pytest

from app.application.use_cases.tasks.assign_task import AssignTask
from app.domain.exceptions import AssigneeNotFound, NotTaskOwner
from tests.fakes import InMemoryNotifier


@pytest.fixture
def assign(tasks, task_lists, users, notifier, uow, clock) -> AssignTask:
    return AssignTask(
        tasks=tasks,
        task_lists=task_lists,
        users=users,
        notifier=notifier,
        uow=uow,
        clock=clock,
    )


def test_assigns_by_email_and_notifies_the_assignee(
    assign, tasks, notifier, task, owner, assignee
):
    assign.execute(
        task_id=task.id, user_id=owner.id, assignee_email="ASSIGNEE@example.com"
    )

    stored = tasks.get(task.id)
    assert stored is not None
    assert stored.assignee_id == assignee.id
    [(notified_task, notified_user)] = notifier.sent
    assert notified_task.id == task.id
    assert notified_user == assignee


def test_notifies_only_after_the_commit(assign, events, task, owner, assignee):
    assign.execute(
        task_id=task.id, user_id=owner.id, assignee_email=assignee.email.value
    )

    assert events == ["commit", "notify"]


def test_assigning_the_same_user_again_does_nothing(
    assign, uow, notifier, assigned_task, owner, assignee
):
    assign.execute(
        task_id=assigned_task.id, user_id=owner.id, assignee_email=assignee.email.value
    )

    assert not uow.committed
    assert notifier.sent == []


def test_reassigning_notifies_the_new_assignee(
    assign, notifier, assigned_task, owner, stranger
):
    assign.execute(
        task_id=assigned_task.id, user_id=owner.id, assignee_email=stranger.email.value
    )

    assert [user for _, user in notifier.sent] == [stranger]


def test_the_owner_assigning_themselves_is_not_notified(
    assign, tasks, notifier, task, owner
):
    assign.execute(task_id=task.id, user_id=owner.id, assignee_email=owner.email.value)

    stored = tasks.get(task.id)
    assert stored is not None
    assert stored.assignee_id == owner.id
    assert notifier.sent == []


@pytest.mark.parametrize("email", ["nobody@example.com", "not-an-email"])
def test_an_unknown_assignee_is_rejected(assign, uow, task, owner, email):
    with pytest.raises(AssigneeNotFound):
        assign.execute(task_id=task.id, user_id=owner.id, assignee_email=email)

    assert not uow.committed


def test_only_the_owner_can_assign(assign, assigned_task, assignee, stranger):
    with pytest.raises(NotTaskOwner):
        assign.execute(
            task_id=assigned_task.id,
            user_id=assignee.id,
            assignee_email=stranger.email.value,
        )


def test_a_failed_notification_keeps_the_assignment(
    tasks, task_lists, users, uow, clock, task, owner, assignee, caplog
):
    assign = AssignTask(
        tasks=tasks,
        task_lists=task_lists,
        users=users,
        notifier=InMemoryNotifier(fail=True),
        uow=uow,
        clock=clock,
    )

    with caplog.at_level(logging.ERROR):
        assign.execute(
            task_id=task.id, user_id=owner.id, assignee_email=assignee.email.value
        )

    stored = tasks.get(task.id)
    assert stored is not None
    assert stored.assignee_id == assignee.id
    assert uow.committed
    assert "the assignment was kept" in caplog.text
