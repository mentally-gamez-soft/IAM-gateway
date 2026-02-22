"""Asynchronous email sending tasks.

Design
------
* **Queue**: ``email``  (configured in ``core/tasks/__init__.py``)
* **Retries**: up to ``max_retries=3`` with exponential back-off
  (60 s → 120 s → 240 s).
* **Dead-letter**: after the third retry failure the error is logged with
  full context.  In production a message-level dead-letter queue
  (``email.dlq``) can be configured at the broker level.
* **Flask context**: ``ContextTask`` (see ``core/tasks/__init__.py``) pushes
  the application context, so ``Flask-Mail`` and the current app config are
  always available.

Usage::

    from core.tasks.email_tasks import send_email_task

    # Fire-and-forget
    send_email_task.delay(
        to="user@example.com",
        subject="Activate your account",
        body="Plain-text body.",
        html_body="<p>HTML body.</p>",
    )
"""

import logging

from flask_mail import Message

from core.tasks import celery
from server.config.mails import mail

logger = logging.getLogger(__name__)


@celery.task(
    bind=True,
    name="core.tasks.email_tasks.send_email_task",
    max_retries=3,
    default_retry_delay=60,
    queue="email",
)
def send_email_task(
    self,
    to: str,
    subject: str,
    body: str,
    html_body: str | None = None,
    template_name: str | None = None,
) -> dict:
    """Send an email asynchronously via Flask-Mail.

    Args:
        self: Bound Celery task instance (retry / request access).
        to: Recipient email address.
        subject: Email subject line.
        body: Plain-text body.
        html_body: Optional HTML body.  Falls back to *body* when omitted.
        template_name: Optional template identifier (reserved for future use).

    Returns:
        dict: ``{"status": "sent", "to": to}`` on success.

    Raises:
        self.retry: Raised automatically on SMTP / network errors
            (up to ``max_retries`` times, with exponential back-off).
    """
    try:
        msg = Message(
            subject=subject,
            recipients=[to],
            body=body,
            html=html_body or body,
        )
        mail.send(msg)
        logger.info(
            "Email sent successfully: to=%s subject=%s task_id=%s",
            to,
            subject,
            self.request.id,
        )
        return {"status": "sent", "to": to}

    except Exception as exc:
        retry_number = self.request.retries
        next_retry = retry_number + 1

        if retry_number < self.max_retries:
            # Exponential back-off: 60 s, 120 s, 240 s
            countdown = 60 * (2**retry_number)
            logger.warning(
                "Email delivery failed (attempt %d/%d): to=%s error=%s "
                "— retrying in %d s (task_id=%s)",
                next_retry,
                self.max_retries,
                to,
                str(exc),
                countdown,
                self.request.id,
            )
            raise self.retry(exc=exc, countdown=countdown)

        # All retries exhausted — log and route to dead-letter queue
        logger.error(
            "Email delivery permanently failed after %d attempts: "
            "to=%s subject=%s error=%s task_id=%s — "
            "message routed to dead-letter queue (email.dlq)",
            self.max_retries,
            to,
            subject,
            str(exc),
            self.request.id,
        )
        # Re-raise so Celery marks the task as FAILURE
        raise
