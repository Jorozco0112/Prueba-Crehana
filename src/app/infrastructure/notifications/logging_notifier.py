import logging

from app.application.ports import TaskAssignmentNotifier
from app.domain.task import Task
from app.domain.user import User

logger = logging.getLogger(__name__)


class LoggingTaskAssignmentNotifier(TaskAssignmentNotifier):
    """Simulated email: builds the message and writes it to the log (DEC-033).

    Replacing it with an SMTP or Slack adapter does not change any use case.
    """

    def notify_assigned(self, task: Task, assignee: User) -> None:
        subject = f"You have been assigned a task: {task.title}"
        body = (
            f"Hi {assignee.full_name},\n\n"
            f"The task '{task.title}' (priority {task.priority}) was assigned to you.\n"
            f"Task ID: {task.id}"
        )
        logger.info(
            "Simulated email sent\nTo: %s\nSubject: %s\n\n%s",
            assignee.email,
            subject,
            body,
        )
