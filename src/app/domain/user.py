from datetime import datetime
from typing import Self
from uuid import UUID, uuid7

from app.domain.entity import Entity
from app.domain.rules import FULL_NAME_MAX_LENGTH, require_text
from app.domain.value_objects import Email


class User(Entity):
    """A registered user. Users own task lists and can be assigned tasks."""

    __slots__ = ("_email", "_full_name", "_password_hash", "_created_at")

    def __init__(
        self,
        *,
        id: UUID,
        email: Email,
        full_name: str,
        password_hash: str,
        created_at: datetime,
    ) -> None:
        super().__init__(id)
        self._email = email
        self._full_name = require_text("full_name", full_name, FULL_NAME_MAX_LENGTH)
        self._password_hash = password_hash
        self._created_at = created_at

    @classmethod
    def register(
        cls, *, email: Email, full_name: str, password_hash: str, now: datetime
    ) -> Self:
        return cls(
            id=uuid7(),
            email=email,
            full_name=full_name,
            password_hash=password_hash,
            created_at=now,
        )

    @property
    def email(self) -> Email:
        return self._email

    @property
    def full_name(self) -> str:
        return self._full_name

    @property
    def password_hash(self) -> str:
        return self._password_hash

    @property
    def created_at(self) -> datetime:
        return self._created_at
