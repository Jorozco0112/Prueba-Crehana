from sqlalchemy.orm import Session

from app.application.ports import UnitOfWork


class SqlAlchemyUnitOfWork(UnitOfWork):
    """The SQLAlchemy session already tracks changes; this exposes when to commit."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def commit(self) -> None:
        self._session.commit()

    def rollback(self) -> None:
        self._session.rollback()
