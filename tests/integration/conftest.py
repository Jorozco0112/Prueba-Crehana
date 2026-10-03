"""Integration tests run against a real PostgreSQL (DEC-034, DEC-035).

The schema is built once per session by running the Alembic migrations, so the
migrations themselves are tested too. Tables are truncated after each test (DEC-036).
"""

from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import Engine, make_url, text
from sqlalchemy.orm import Session

from app.infrastructure.config import get_database_settings
from app.infrastructure.db.session import get_engine, get_session_factory

ALEMBIC_INI = Path(__file__).resolve().parents[2] / "alembic.ini"


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    url = make_url(get_database_settings().database_url)
    if not (url.database or "").endswith("_test"):
        pytest.exit(f"Refusing to run integration tests against '{url.database}'.")

    engine = get_engine()
    with engine.begin() as connection:
        connection.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        connection.execute(text("CREATE SCHEMA public"))

    config = Config(str(ALEMBIC_INI))
    config.attributes["configure_logger"] = False
    command.upgrade(config, "head")
    yield engine


@pytest.fixture(autouse=True)
def clean_database(engine: Engine) -> Iterator[None]:
    yield
    with engine.begin() as connection:
        connection.execute(text("TRUNCATE tasks, task_lists, users CASCADE"))


@pytest.fixture
def session(engine: Engine) -> Iterator[Session]:
    session = get_session_factory()()
    yield session
    session.close()
