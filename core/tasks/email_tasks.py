"""Asynchronous email sending tasks.

Design
------
* **Queue**: ``email``  (configured in ``core/tasks/__init__.py``)
* **Retry policy (tenacity)**: up to 3 retries with exponential back-off
  (60 s → 120 s → 240 s). Only transient network/IO errors trigger retries;
  permanent errors (auth, bad recipient, configuration) propagate immediately.
* **Circuit breaker (pybreaker)**: wraps the entire tenacity-managed delivery
  sequence.  One *task-level* failure (even after 4 attempts internally) counts
  as a single failure increment.  After ``SMTP_FAIL_MAX`` consecutive task
  failures the breaker trips and rejects new tasks immediately, letting the
  worker queue drain and the mail server recover.
* **Dead-letter**: after all retries are exhausted (or the circuit is open)
  the error is logged with full context and the task is marked ``FAILURE``.
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

import pybreaker
from flask_mail import Message
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from core.tasks import celery
from server.config.mails import mail

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Transient error types that tenacity should retry.
# Permanent errors (RuntimeError, ValueError, …) propagate immediately.
# ---------------------------------------------------------------------------
_RETRYABLE_EXCEPTIONS = (ConnectionError, TimeoutError, OSError, IOError)

# ---------------------------------------------------------------------------
# SMTP circuit breaker
#
# Trips after SMTP_FAIL_MAX consecutive *task-level* failures — i.e. after a
# task has already exhausted all of its tenacity retries.  One task execution
# (regardless of how many internal attempts tenacity made) counts as a single
# failure increment.  After SMTP_RESET_TIMEOUT seconds in the OPEN state the
# breaker moves to HALF-OPEN and lets one probe attempt through.
# ---------------------------------------------------------------------------
SMTP_FAIL_MAX = 5
SMTP_RESET_TIMEOUT = 60

smtp_breaker = pybreaker.CircuitBreaker(
    fail_max=SMTP_FAIL_MAX,
    reset_timeout=SMTP_RESET_TIMEOUT,
    name="smtp",
)


# ---------------------------------------------------------------------------
# Per-attempt delivery helper — tenacity owns the retry / back-off policy
# ---------------------------------------------------------------------------
@retry(
    reraise=True,
    stop=stop_after_attempt(4),  # 1 initial + 3 retries
    wait=wait_exponential(
        multiplier=60, min=60, max=240
    ),  # 60 s → 120 s → 240 s
    retry=retry_if_exception_type(_RETRYABLE_EXCEPTIONS),
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
def _deliver(msg: Message) -> None:
    """Single delivery attempt; tenacity retries on transient errors only."""
    mail.send(msg)


def _send_message(msg: Message) -> None:
    """Guard the tenacity-retried delivery with the SMTP circuit breaker.

    The breaker wraps the *entire* retry sequence so one task-level failure
    (possibly spanning up to 4 internal attempts) counts as a single failure
    increment towards ``SMTP_FAIL_MAX``.
    """
    smtp_breaker.call(_deliver, msg)


@celery.task(
    bind=True,
    name="core.tasks.email_tasks.send_email_task",
    max_retries=0,  # tenacity owns retries; Celery is the outer shell only
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
        self: Bound Celery task instance.
        to: Recipient email address.
        subject: Email subject line.
        body: Plain-text body.
        html_body: Optional HTML body.  Falls back to *body* when omitted.
        template_name: Optional template identifier (reserved for future use).

    Returns:
        dict: ``{"status": "sent", "to": to}`` on success.

    Raises:
        pybreaker.CircuitBreakerError: When the SMTP circuit breaker is open.
        Exception: When all tenacity retries are exhausted.
    """
    try:
        msg = Message(
            subject=subject,
            recipients=[to],
            body=body,
            html=html_body or body,
        )
        _send_message(msg)
        logger.info(
            "Email sent successfully: to=%s subject=%s task_id=%s",
            to,
            subject,
            self.request.id,
        )
        return {"status": "sent", "to": to}

    except pybreaker.CircuitBreakerError as exc:
        logger.error(
            "SMTP circuit breaker OPEN — email not sent: "
            "to=%s task_id=%s error=%s",
            to,
            self.request.id,
            str(exc),
        )
        raise

    except Exception as exc:
        # Tenacity has already exhausted all retries at this point.
        logger.error(
            "Email delivery permanently failed after retries: "
            "to=%s subject=%s error=%s task_id=%s — "
            "message routed to dead-letter queue (email.dlq)",
            to,
            subject,
            str(exc),
            self.request.id,
        )
        raise
