from datetime import datetime
from typing import Self
from uuid import UUID, uuid7

from app.domain.entity import Entity
from app.domain.rules import LIST_NAME_MAX_LENGTH, require_text


class TaskList(Entity):
    """A list of tasks. Only its owner can see or modify it (DEC-002).

    Tasks are a separate aggregate that reference the list by ID (DEC-003).
    """

    __slots__ = ("_owner_id", "_name", "_created_at", "_updated_at")

    def __init__(
        self,
        *,
        id: UUID,
        owner_id: UUID,
        name: str,
        created_at: datetime,
        updated_at: datetime,
    ) -> None:
        super().__init__(id)
        self._owner_id = owner_id
        self._name = require_text("name", name, LIST_NAME_MAX_LENGTH)
        self._created_at = created_at
        self._updated_at = updated_at

    @classmethod
    def create(cls, *, owner_id: UUID, name: str, now: datetime) -> Self:
        return cls(
            id=uuid7(),
            owner_id=owner_id,
            name=name,
            created_at=now,
            updated_at=now,
        )

    @property
    def owner_id(self) -> UUID:
        return self._owner_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    def is_owned_by(self, user_id: UUID) -> bool:
        return self._owner_id == user_id

    def rename(self, name: str, *, at: datetime) -> None:
        self._name = require_text("name", name, LIST_NAME_MAX_LENGTH)
        self._updated_at = at
