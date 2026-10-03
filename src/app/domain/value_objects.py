"""Value objects: no identity, compared by value, immutable and self-validating."""

from decimal import ROUND_HALF_UP, Decimal
from enum import StrEnum
from typing import Self

from app.domain.exceptions import InvalidFieldValue


class TaskStatus(StrEnum):
    """Any transition between statuses is allowed (DEC-004)."""

    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"


class Priority(StrEnum):
    """Task priority. ``rank`` gives the order of importance (DEC-005)."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"

    @property
    def rank(self) -> int:
        return _PRIORITY_RANKS[self]

    @classmethod
    def from_rank(cls, rank: int) -> Priority:
        for priority, priority_rank in _PRIORITY_RANKS.items():
            if priority_rank == rank:
                return priority
        raise ValueError(f"Unknown priority rank: {rank}")


_PRIORITY_RANKS: dict[Priority, int] = {
    Priority.LOW: 0,
    Priority.MEDIUM: 1,
    Priority.HIGH: 2,
    Priority.URGENT: 3,
}


class Email:
    """An email address, normalized so ``Ana@X.com`` and ``ana@x.com`` are equal."""

    MAX_LENGTH = 254

    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        normalized = value.strip().lower()
        local, separator, domain = normalized.partition("@")
        if not separator or not local or "." not in domain or "@" in domain:
            raise InvalidFieldValue("email", "it is not a valid email address.")
        if len(normalized) > self.MAX_LENGTH:
            raise InvalidFieldValue(
                "email", f"it must have at most {self.MAX_LENGTH} characters."
            )
        self._value = normalized

    @property
    def value(self) -> str:
        return self._value

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Email) and other._value == self._value

    def __hash__(self) -> int:
        return hash(self._value)

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"Email({self._value!r})"


class CompletionPercentage:
    """Completion of a task list: completed tasks over all its tasks (DEC-008).

    An empty list is at 0%; ``total`` lets clients tell it apart from a list with no
    progress.
    """

    __slots__ = ("_completed", "_total")

    _TWO_DECIMALS = Decimal("0.01")

    def __init__(self, completed: int, total: int) -> None:
        if total < 0 or completed < 0 or completed > total:
            raise ValueError(
                f"Inconsistent task counts: completed={completed}, total={total}"
            )
        self._completed = completed
        self._total = total

    @classmethod
    def from_counts(cls, completed: int, total: int) -> Self:
        return cls(completed=completed, total=total)

    @property
    def completed(self) -> int:
        return self._completed

    @property
    def total(self) -> int:
        return self._total

    @property
    def percentage(self) -> Decimal:
        if self._total == 0:
            return Decimal("0.00")
        ratio = Decimal(self._completed) * 100 / Decimal(self._total)
        return ratio.quantize(self._TWO_DECIMALS, rounding=ROUND_HALF_UP)

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, CompletionPercentage)
            and other._completed == self._completed
            and other._total == self._total
        )

    def __hash__(self) -> int:
        return hash((self._completed, self._total))

    def __repr__(self) -> str:
        return f"CompletionPercentage({self._completed}/{self._total})"
