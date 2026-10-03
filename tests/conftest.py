import os

import pytest

# Defaults for local runs; docker-compose and CI provide their own values. The test
# database is the `db-test` service, published on port 5433 (DEC-035).
os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://todo:todo@localhost:5433/todo_test"
)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-with-at-least-32-characters")


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Mark each test as `unit` or `integration` from its folder (DEC-034)."""
    for item in items:
        if "integration" in item.path.parts:
            item.add_marker(pytest.mark.integration)
        elif "unit" in item.path.parts:
            item.add_marker(pytest.mark.unit)
