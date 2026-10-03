from datetime import timedelta

import pytest

from app.application.dto import PageRequest
from app.domain.exceptions import EmailAlreadyRegistered, TaskListNotFound
from app.domain.value_objects import Email
from app.infrastructure.db.repositories import (
    SqlAlchemyTaskListRepository,
    SqlAlchemyTaskRepository,
    SqlAlchemyUserRepository,
)
from app.infrastructure.db.session import get_session_factory
from app.infrastructure.db.unit_of_work import SqlAlchemyUnitOfWork
from tests.factories import NOW, make_task, make_task_list, make_user


class TestUserRepository:
    def test_round_trip(self, session):
        users = SqlAlchemyUserRepository(session)
        user = make_user(email="ana@example.com")
        users.add(user)
        session.commit()
        session.expunge_all()

        stored = users.get(user.id)

        assert stored == user
        assert stored is not None
        assert stored.email == Email("ana@example.com")
        assert stored.created_at == user.created_at

    def test_get_by_email_uses_the_normalized_address(self, session):
        users = SqlAlchemyUserRepository(session)
        user = make_user(email="Ana@Example.com")
        users.add(user)

        assert users.get_by_email(Email("ANA@example.COM")) == user
        assert users.get_by_email(Email("bob@example.com")) is None

    def test_the_unique_constraint_becomes_a_domain_error(self, session):
        """Two concurrent registrations can both pass the use case check."""
        users = SqlAlchemyUserRepository(session)
        users.add(make_user(email="ana@example.com"))

        with pytest.raises(EmailAlreadyRegistered):
            users.add(make_user(email="ana@example.com"))


class TestTaskListRepository:
    @pytest.fixture
    def owner(self, session):
        owner = make_user()
        SqlAlchemyUserRepository(session).add(owner)
        return owner

    def test_add_update_and_get(self, session, owner):
        task_lists = SqlAlchemyTaskListRepository(session)
        task_list = make_task_list(owner_id=owner.id)
        task_lists.add(task_list)
        session.commit()

        task_list.rename("Weekend", at=NOW + timedelta(hours=1))
        task_lists.update(task_list)
        session.commit()
        session.expunge_all()

        stored = task_lists.get(task_list.id)
        assert stored is not None
        assert stored.name == "Weekend"
        assert stored.updated_at == NOW + timedelta(hours=1)

    def test_updating_a_missing_list_fails(self, session, owner):
        with pytest.raises(TaskListNotFound):
            SqlAlchemyTaskListRepository(session).update(
                make_task_list(owner_id=owner.id)
            )

    def test_deleting_a_list_deletes_its_tasks(self, session, owner):
        task_lists = SqlAlchemyTaskListRepository(session)
        tasks = SqlAlchemyTaskRepository(session)
        task_list = make_task_list(owner_id=owner.id)
        task_lists.add(task_list)
        session.flush()
        task = make_task(list_id=task_list.id)
        tasks.add(task)
        session.commit()

        task_lists.delete(task_list)
        session.commit()
        session.expunge_all()

        assert task_lists.get(task_list.id) is None
        assert tasks.get(task.id) is None

    def test_lists_the_owners_lists_newest_first_with_pagination(self, session, owner):
        task_lists = SqlAlchemyTaskListRepository(session)
        other_owner = make_user(email="bob@example.com")
        SqlAlchemyUserRepository(session).add(other_owner)
        created = [
            make_task_list(owner_id=owner.id, name=f"List {i}", now=NOW + timedelta(i))
            for i in range(3)
        ]
        for task_list in [*created, make_task_list(owner_id=other_owner.id)]:
            task_lists.add(task_list)
        session.commit()

        first = task_lists.list_by_owner(owner.id, PageRequest(limit=2, offset=0))
        second = task_lists.list_by_owner(owner.id, PageRequest(limit=2, offset=2))

        assert [item.name for item in first.items] == ["List 2", "List 1"]
        assert [item.name for item in second.items] == ["List 0"]
        assert first.total == second.total == 3


class TestUnitOfWork:
    def test_rollback_discards_pending_changes(self, session):
        users = SqlAlchemyUserRepository(session)
        uow = SqlAlchemyUnitOfWork(session)
        user = make_user()
        users.add(user)

        uow.rollback()

        assert users.get(user.id) is None

    def test_commit_makes_changes_visible_to_other_sessions(self, session):
        user = make_user()
        SqlAlchemyUserRepository(session).add(user)

        SqlAlchemyUnitOfWork(session).commit()

        with get_session_factory()() as other_session:
            assert SqlAlchemyUserRepository(other_session).get(user.id) == user
