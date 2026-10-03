from uuid import UUID


class Entity:
    """Base class for entities: two entities are equal when they have the same ID."""

    __slots__ = ("_id",)

    def __init__(self, id: UUID) -> None:
        self._id = id

    @property
    def id(self) -> UUID:
        return self._id

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Entity) or type(other) is not type(self):
            return False
        return other._id == self._id

    def __hash__(self) -> int:
        return hash(self._id)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(id={self._id})"
