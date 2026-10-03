"""SQLAlchemy models, kept separate from the domain entities (DEC-016)."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    MetaData,
    SmallInteger,
    String,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.domain.rules import (
    DESCRIPTION_MAX_LENGTH,
    FULL_NAME_MAX_LENGTH,
    LIST_NAME_MAX_LENGTH,
    TITLE_MAX_LENGTH,
)
from app.domain.value_objects import Email

# Predictable constraint names, so migrations and error handling can refer to them.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

USERS_EMAIL_UNIQUE_CONSTRAINT = "uq_users_email"


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class UserModel(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(Email.MAX_LENGTH), unique=True)
    full_name: Mapped[str] = mapped_column(String(FULL_NAME_MAX_LENGTH))
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class TaskListModel(Base):
    __tablename__ = "task_lists"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    owner_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(LIST_NAME_MAX_LENGTH))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class TaskModel(Base):
    __tablename__ = "tasks"
    __table_args__ = (
        # Stored as an integer so it can be sorted by importance (DEC-019).
        CheckConstraint("priority BETWEEN 0 AND 3", name="priority_range"),
        # Plain text instead of a native ENUM, which needs ALTER TYPE to grow.
        CheckConstraint(
            "status IN ('PENDING', 'IN_PROGRESS', 'COMPLETED')", name="status_valid"
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True)
    # Deleting a list deletes its tasks in a single statement (DEC-003).
    list_id: Mapped[UUID] = mapped_column(
        ForeignKey("task_lists.id", ondelete="CASCADE"), index=True
    )
    title: Mapped[str] = mapped_column(String(TITLE_MAX_LENGTH))
    description: Mapped[str | None] = mapped_column(String(DESCRIPTION_MAX_LENGTH))
    priority: Mapped[int] = mapped_column(SmallInteger)
    status: Mapped[str] = mapped_column(String(20))
    assignee_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
