from datetime import timedelta
from uuid import uuid7

import pytest

from app.domain.exceptions import InvalidFieldValue
from app.domain.value_objects import Email
from tests.factories import NOW, make_task_list, make_user


class TestTaskList:
    def test_create(self):
        owner_id = uuid7()

        task_list = make_task_list(owner_id=owner_id, name="  Groceries ")

        assert task_list.name == "Groceries"
        assert task_list.owner_id == owner_id
        assert task_list.created_at == task_list.updated_at == NOW

    def test_only_the_owner_owns_it(self):
        owner_id = uuid7()
        task_list = make_task_list(owner_id=owner_id)

        assert task_list.is_owned_by(owner_id)
        assert not task_list.is_owned_by(uuid7())

    def test_rename(self):
        task_list = make_task_list(owner_id=uuid7())
        later = NOW + timedelta(minutes=5)

        task_list.rename("Weekend", at=later)

        assert task_list.name == "Weekend"
        assert task_list.updated_at == later

    @pytest.mark.parametrize("name", ["", "   ", "x" * 101])
    def test_rejects_invalid_names(self, name):
        with pytest.raises(InvalidFieldValue) as error:
            make_task_list(owner_id=uuid7(), name=name)

        assert error.value.field == "name"


class TestUser:
    def test_register(self):
        user = make_user(email="Ana@Example.com", full_name=" Ana Torres ")

        assert user.email == Email("ana@example.com")
        assert user.full_name == "Ana Torres"
        assert user.password_hash == "hashed::correct-horse"
        assert user.created_at == NOW

    def test_rejects_a_blank_full_name(self):
        with pytest.raises(InvalidFieldValue) as error:
            make_user(full_name="  ")

        assert error.value.field == "full_name"
