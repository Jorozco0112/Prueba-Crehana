from datetime import datetime
from typing import Self
from uuid import UUID, uuid7

from app.domain.entity import Entity
from app.domain.rules import (
    DESCRIPTION_MAX_LENGTH,
    TITLE_MAX_LENGTH,
    optional_text,
    require_text,
)
from app.domain.value_objects import Priority, TaskStatus


class Task(Entity):
    """A task inside a task list.

    State that carries rules (status, assignee) is read-only and changes only through
    methods, so ``completed_at`` can never get out of sync with the status (DEC-010).
    The current time is always received as a parameter (DEC-038).
    """

    __slots__ = (
        "_list_id",
        "_title",
        "_description",
        "_priority",
        "_status",
        "_assignee_id",
        "_created_at",
        "_updated_at",
        "_completed_at",
    )

    def __init__(
        self,
        *,
        id: UUID,
        list_id: UUID,
        title: str,
        description: str | None,
        priority: Priority,
        status: TaskStatus,
        assignee_id: UUID | None,
        created_at: datetime,
        updated_at: datetime,
        completed_at: datetime | None,
    ) -> None:
        super().__init__(id)
        self._list_id = list_id
        self._title = require_text("title", title, TITLE_MAX_LENGTH)
        self._description = optional_text(
            "description", description, DESCRIPTION_MAX_LENGTH
        )
        self._priority = priority
        self._status = status
        self._assignee_id = assignee_id
        self._created_at = created_at
        self._updated_at = updated_at
        self._completed_at = completed_at

    @classmethod
    def create(
        cls,
        *,
        list_id: UUID,
        title: str,
        description: str | None,
        priority: Priority,
        now: datetime,
    ) -> Self:
        """New tasks always start as ``PENDING`` and unassigned (DEC-029)."""
        return cls(
            id=uuid7(),
            list_id=list_id,
            title=title,
            description=description,
            priority=priority,
            status=TaskStatus.PENDING,
            assignee_id=None,
            created_at=now,
            updated_at=now,
            completed_at=None,
        )

    # --- Read-only state ----------------------------------------------------------

    @property
    def list_id(self) -> UUID:
        return self._list_id

    @property
    def title(self) -> str:
        return self._title

    @property
    def description(self) -> str | None:
        return self._description

    @property
    def priority(self) -> Priority:
        return self._priority

    @property
    def status(self) -> TaskStatus:
        return self._status

    @property
    def assignee_id(self) -> UUID | None:
        return self._assignee_id

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        return self._updated_at

    @property
    def completed_at(self) -> datetime | None:
        return self._completed_at

    # --- Behavior -----------------------------------------------------------------

    def is_assigned_to(self, user_id: UUID) -> bool:
        return self._assignee_id == user_id

    def rename(self, title: str, *, at: datetime) -> None:
        self._title = require_text("title", title, TITLE_MAX_LENGTH)
        self._updated_at = at

    def describe(self, description: str | None, *, at: datetime) -> None:
        self._description = optional_text(
            "description", description, DESCRIPTION_MAX_LENGTH
        )
        self._updated_at = at

    def prioritize(self, priority: Priority, *, at: datetime) -> None:
        self._priority = priority
        self._updated_at = at

    def change_status(self, new_status: TaskStatus, *, at: datetime) -> None:
        """Move to any status (DEC-004). Repeating the current status does nothing."""
        if new_status == self._status:
            return
        self._status = new_status
        self._completed_at = at if new_status == TaskStatus.COMPLETED else None
        self._updated_at = at

    def assign_to(self, user_id: UUID, *, at: datetime) -> bool:
        """Assign a responsible user. Returns ``False`` if nothing changed (DEC-023)."""
        if self._assignee_id == user_id:
            return False
        self._assignee_id = user_id
        self._updated_at = at
        return True

    def unassign(self, *, at: datetime) -> None:
        if self._assignee_id is None:
            return
        self._assignee_id = None
        self._updated_at = at
