import logging
from datetime import UTC
from uuid import uuid7

from app.domain.value_objects import Priority
from app.infrastructure.clock import SystemClock
from app.infrastructure.notifications.logging_notifier import (
    LoggingTaskAssignmentNotifier,
)
from tests.factories import make_task, make_user


def test_the_simulated_email_is_written_to_the_log(caplog):
    task = make_task(list_id=uuid7(), title="Prepare demo", priority=Priority.HIGH)
    assignee = make_user(email="adam@example.com", full_name="Adam")

    with caplog.at_level(logging.INFO):
        LoggingTaskAssignmentNotifier().notify_assigned(task, assignee)

    assert "To: adam@example.com" in caplog.text
    assert "Subject: You have been assigned a task: Prepare demo" in caplog.text
    assert "Hi Adam" in caplog.text


def test_the_system_clock_returns_utc_time():
    assert SystemClock().now().tzinfo is UTC
