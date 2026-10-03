from datetime import timedelta

import pytest

from app.application.dto import PageRequest
from app.application.use_cases.task_lists.create_task_list import CreateTaskList
from app.application.use_cases.task_lists.delete_task_list import DeleteTaskList
from app.application.use_cases.task_lists.get_task_list import GetTaskList
from app.application.use_cases.task_lists.list_task_lists import ListTaskLists
from app.application.use_cases.task_lists.update_task_list import UpdateTaskList
from app.domain.exceptions import TaskListNotFound
from tests.factories import NOW, make_task_list


class TestCreateTaskList:
    def test_creates_a_list_owned_by_the_user(self, task_lists, uow, clock, owner):
        use_case = CreateTaskList(task_lists=task_lists, uow=uow, clock=clock)

        task_list = use_case.execute(owner_id=owner.id, name="Groceries")

        assert task_lists.get(task_list.id) == task_list
        assert task_list.owner_id == owner.id
        assert task_list.created_at == clock.now()
        assert uow.committed


class TestGetTaskList:
    def test_the_owner_can_get_it(self, task_lists, task_list, owner):
        use_case = GetTaskList(task_lists=task_lists)

        assert use_case.execute(list_id=task_list.id, user_id=owner.id) == task_list

    def test_another_user_gets_not_found(self, task_lists, task_list, stranger):
        use_case = GetTaskList(task_lists=task_lists)

        with pytest.raises(TaskListNotFound):
            use_case.execute(list_id=task_list.id, user_id=stranger.id)


class TestListTaskLists:
    def test_returns_only_the_users_lists_newest_first(
        self, task_lists, owner, stranger
    ):
        older = make_task_list(owner_id=owner.id, name="Older", now=NOW)
        newer = make_task_list(
            owner_id=owner.id, name="Newer", now=NOW + timedelta(hours=1)
        )
        for task_list in (older, newer, make_task_list(owner_id=stranger.id)):
            task_lists.add(task_list)

        page = ListTaskLists(task_lists=task_lists).execute(
            owner_id=owner.id, page=PageRequest(limit=10, offset=0)
        )

        assert page.items == [newer, older]
        assert page.total == 2

    def test_paginates(self, task_lists, owner):
        for hour in range(3):
            task_lists.add(
                make_task_list(owner_id=owner.id, now=NOW + timedelta(hours=hour))
            )

        page = ListTaskLists(task_lists=task_lists).execute(
            owner_id=owner.id, page=PageRequest(limit=2, offset=2)
        )

        assert len(page.items) == 1
        assert (page.total, page.limit, page.offset) == (3, 2, 2)


class TestUpdateTaskList:
    def test_renames_the_list(self, task_lists, uow, clock, task_list, owner):
        clock.advance(minutes=10)
        use_case = UpdateTaskList(task_lists=task_lists, uow=uow, clock=clock)

        updated = use_case.execute(
            list_id=task_list.id, user_id=owner.id, changes={"name": "Weekend"}
        )

        stored = task_lists.get(task_list.id)
        assert stored is not None
        assert stored.name == updated.name == "Weekend"
        assert stored.updated_at == clock.now()
        assert uow.committed

    def test_no_changes_means_no_commit(self, task_lists, uow, clock, task_list, owner):
        use_case = UpdateTaskList(task_lists=task_lists, uow=uow, clock=clock)

        use_case.execute(list_id=task_list.id, user_id=owner.id, changes={})

        assert not uow.committed

    def test_another_user_gets_not_found(
        self, task_lists, uow, clock, task_list, stranger
    ):
        use_case = UpdateTaskList(task_lists=task_lists, uow=uow, clock=clock)

        with pytest.raises(TaskListNotFound):
            use_case.execute(
                list_id=task_list.id, user_id=stranger.id, changes={"name": "Mine"}
            )


class TestDeleteTaskList:
    def test_deletes_the_list(self, task_lists, uow, task_list, owner):
        DeleteTaskList(task_lists=task_lists, uow=uow).execute(
            list_id=task_list.id, user_id=owner.id
        )

        assert task_lists.get(task_list.id) is None
        assert uow.committed

    def test_another_user_gets_not_found(self, task_lists, uow, task_list, stranger):
        with pytest.raises(TaskListNotFound):
            DeleteTaskList(task_lists=task_lists, uow=uow).execute(
                list_id=task_list.id, user_id=stranger.id
            )

        assert task_lists.get(task_list.id) is not None
