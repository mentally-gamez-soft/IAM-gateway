"""Test suite for asynchronous email task dispatch and failure handling.

Test coverage (TASK-015-7)
--------------------------
 1.  Signup route dispatches ``send_email_task.delay`` (called once).
 2.  ``USE_ASYNC_EMAIL=False`` — signup does *not* dispatch the task.
 3.  ``send_email_task`` succeeds when ``mail.send`` works.
 4.  HTTP 200 is returned before email delivery completes.
 5.  ``send_email_task`` retries on transient SMTP failure.
 6.  ``send_email_task`` retries exactly 3 times (4 calls total, via tenacity).
 7.  ``send_email_task`` re-raises immediately on non-retryable exception.
 8.  Password-reset helper dispatches ``send_email_task.delay`` when async.
 9.  Password-reset helper falls back to synchronous send when not async.
10.  Signup response contains the expected ``user`` and ``jwt`` keys.
11.  Circuit breaker open — task fails immediately without calling mail.send.
12.  Non-retryable exception (RuntimeError) does not trigger retries.

Config notes (config/testing.py)
----------------------------------
* ``CELERY_TASK_ALWAYS_EAGER = True``     — tasks execute synchronously.
* ``CELERY_TASK_EAGER_PROPAGATES = True`` — exceptions propagate to tests.
* ``USE_ASYNC_EMAIL = False``             — email dispatch off by default.

Retry-related notes
-------------------
With pybreaker + tenacity owning retries, Celery's ``max_retries=0`` means
``self.retry()`` is never called.  tenacity sleeps are patched via
``time.sleep`` to keep tests instant.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

import pybreaker

from tests import BaseTestClass

# ---------------------------------------------------------------------------
# Shared test fixtures
# ---------------------------------------------------------------------------

_EMAIL_TASK_PATH = "core.tasks.email_tasks.send_email_task"
_MAIL_PATH = "core.tasks.email_tasks.mail"

_VALID_EMAIL_KWARGS = dict(
    to="recipient@example.com",
    subject="Test Subject",
    body="Plain text body.",
    html_body="<p>HTML body.</p>",
)

_SIGNUP_PAYLOAD = dict(
    username="new_async_user",
    email="new_async_user@example.com",
    password="P@ssw0rd!123",
    role="user",
)


# ---------------------------------------------------------------------------
# 1, 2, 4, 10 — Signup route email dispatch gating
# ---------------------------------------------------------------------------


class TestSignupEmailDispatch(BaseTestClass):
    """Verify the signup route correctly gates async email dispatch."""

    def setUp(self):
        super().setUp()
        self._original_use_async_email = self.app.config.get(
            "USE_ASYNC_EMAIL", False
        )

    def tearDown(self):
        self.app.config["USE_ASYNC_EMAIL"] = self._original_use_async_email
        super().tearDown()

    @patch(_EMAIL_TASK_PATH)
    def test_signup_dispatches_email_task_when_async_enabled(self, mock_task):
        """When USE_ASYNC_EMAIL is True, signup must call
        send_email_task.delay exactly once with the user email."""
        mock_task.delay = MagicMock()
        self.app.config["USE_ASYNC_EMAIL"] = True

        res = self.client.post("/signup", json=_SIGNUP_PAYLOAD)

        self.assertEqual(200, res.status_code)
        mock_task.delay.assert_called_once()
        args, kwargs = mock_task.delay.call_args
        to_arg = args[0] if args else kwargs.get("to")
        self.assertEqual(_SIGNUP_PAYLOAD["email"], to_arg)

    @patch(_EMAIL_TASK_PATH)
    def test_signup_does_not_dispatch_task_when_async_disabled(
        self, mock_task
    ):
        """When USE_ASYNC_EMAIL is False, signup must NOT call
        send_email_task.delay."""
        mock_task.delay = MagicMock()
        self.app.config["USE_ASYNC_EMAIL"] = False

        payload = dict(
            username="sync_user",
            email="sync_user@example.com",
            password="P@ssw0rd!123",
            role="user",
        )
        res = self.client.post("/signup", json=payload)

        self.assertEqual(200, res.status_code)
        mock_task.delay.assert_not_called()

    @patch(_EMAIL_TASK_PATH)
    def test_signup_returns_200_before_email_sent(self, mock_task):
        """Signup must return HTTP 200 immediately — email is fire-and-forget."""
        mock_task.delay = MagicMock()
        self.app.config["USE_ASYNC_EMAIL"] = True

        res = self.client.post("/signup", json=_SIGNUP_PAYLOAD)

        self.assertEqual(200, res.status_code)

    @patch(_EMAIL_TASK_PATH)
    def test_signup_response_contains_expected_keys(self, mock_task):
        """Signup response body must include ``data.user`` and ``data.jwt``
        even when an email task has been queued."""
        mock_task.delay = MagicMock()
        self.app.config["USE_ASYNC_EMAIL"] = True

        res = self.client.post("/signup", json=_SIGNUP_PAYLOAD)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIn("data", data)
        self.assertIn("user", data["data"])
        self.assertIn("jwt", data["data"])


# ---------------------------------------------------------------------------
# 3, 5, 6, 7, 11, 12 — send_email_task unit tests
# ---------------------------------------------------------------------------


class TestSendEmailTask(BaseTestClass):
    """Unit tests that exercise send_email_task directly via .apply()."""

    def setUp(self):
        super().setUp()
        # Reset the circuit breaker to CLOSED before each test so previous
        # failures do not bleed into the next test.
        from core.tasks.email_tasks import smtp_breaker

        smtp_breaker.close()

    def tearDown(self):
        from core.tasks.email_tasks import smtp_breaker

        smtp_breaker.close()
        super().tearDown()

    def _apply_task(self, **overrides):
        """Run the task synchronously and return the AsyncResult.

        tenacity retries are instant because ``time.sleep`` is patched by
        individual test methods that exercise the retry path.
        """
        from core.tasks.email_tasks import send_email_task

        kwargs = {**_VALID_EMAIL_KWARGS, **overrides}
        return send_email_task.apply(kwargs=kwargs, throw=True)

    @patch(_MAIL_PATH)
    def test_task_succeeds_with_valid_params(self, mock_mail):
        """Task returns ``{"status": "sent", "to": ...}`` when mail.send works."""
        mock_mail.send = MagicMock()

        result = self._apply_task()

        self.assertEqual("sent", result.result["status"])
        self.assertEqual(_VALID_EMAIL_KWARGS["to"], result.result["to"])
        mock_mail.send.assert_called_once()

    @patch("time.sleep")
    @patch(_MAIL_PATH)
    def test_task_retries_on_smtp_failure(self, mock_mail, mock_sleep):
        """Task must raise an exception when mail.send fails with a
        transient error; tenacity sleep is patched to keep the test instant."""
        mock_mail.send.side_effect = ConnectionError("SMTP unreachable")

        with self.assertRaises(Exception):
            self._apply_task()

    @patch("time.sleep")
    @patch(_MAIL_PATH)
    def test_task_retries_exactly_max_retries_times(
        self, mock_mail, mock_sleep
    ):
        """mail.send must be called exactly 4 times (1 initial + 3 tenacity
        retries) before the exception propagates.

        tenacity owns the retry cycle; Celery’s max_retries is 0.
        ``time.sleep`` is patched so the exponential back-off is instant.
        """
        mock_mail.send.side_effect = OSError("Persistent SMTP failure")

        with self.assertRaises(OSError):
            self._apply_task()

        self.assertEqual(4, mock_mail.send.call_count)
        # tenacity must have invoked the back-off sleep 3 times
        self.assertEqual(3, mock_sleep.call_count)

    @patch(_MAIL_PATH)
    def test_task_re_raises_immediately_on_non_retryable_exception(
        self, mock_mail
    ):
        """RuntimeError is not in _RETRYABLE_EXCEPTIONS so tenacity must
        propagate it immediately without any retry attempt."""
        mock_mail.send.side_effect = RuntimeError("Auth failure")

        with self.assertRaises(RuntimeError):
            self._apply_task()

        # Only the single initial attempt — no retries
        self.assertEqual(1, mock_mail.send.call_count)

    def test_task_fails_immediately_when_circuit_is_open(self):
        """When the SMTP circuit breaker is OPEN the task must raise
        ``CircuitBreakerError`` without making any call to mail.send."""
        from core.tasks.email_tasks import send_email_task, smtp_breaker

        smtp_breaker.open()  # force breaker to OPEN state

        with patch(_MAIL_PATH) as mock_mail:
            mock_mail.send = MagicMock()
            # throw=False: prevents eager propagation so we can inspect result
            result = send_email_task.apply(
                kwargs=_VALID_EMAIL_KWARGS, throw=False
            )

        self.assertTrue(result.failed())
        self.assertIsInstance(result.info, pybreaker.CircuitBreakerError)
        mock_mail.send.assert_not_called()

    @patch(_MAIL_PATH)
    def test_task_sends_to_correct_recipient(self, mock_mail):
        """The Message passed to mail.send must include the correct recipient."""
        mock_mail.send = MagicMock()

        self._apply_task()

        sent_message = mock_mail.send.call_args[0][0]
        self.assertIn(_VALID_EMAIL_KWARGS["to"], sent_message.recipients)

    @patch(_MAIL_PATH)
    def test_task_includes_html_body_in_message(self, mock_mail):
        """The Message must carry the HTML body when one is provided."""
        mock_mail.send = MagicMock()

        self._apply_task(html_body="<p>Test HTML</p>")

        sent_message = mock_mail.send.call_args[0][0]
        self.assertIn("<p>Test HTML</p>", sent_message.html)


# ---------------------------------------------------------------------------
# 8, 9 — Password-reset email — async vs synchronous dispatch
# ---------------------------------------------------------------------------


class TestPasswordResetEmailDispatch(BaseTestClass):
    """Verify password-reset email routing based on USE_ASYNC_EMAIL."""

    def setUp(self):
        super().setUp()
        self._original_use_async_email = self.app.config.get(
            "USE_ASYNC_EMAIL", False
        )

    def tearDown(self):
        self.app.config["USE_ASYNC_EMAIL"] = self._original_use_async_email
        super().tearDown()

    def _make_mock_user(self, email="user@example.com", username="testuser"):
        user = MagicMock()
        user.email = email
        user.username = username
        return user

    @patch(_EMAIL_TASK_PATH)
    def test_password_reset_dispatches_task_when_async_enabled(
        self, mock_task
    ):
        """send_password_reset_email must call send_email_task.delay when
        USE_ASYNC_EMAIL is True."""
        mock_task.delay = MagicMock()
        self.app.config["USE_ASYNC_EMAIL"] = True

        user = self._make_mock_user()

        with self.app.app_context():
            with self.app.test_request_context("/"):
                with patch(
                    "server.config.mails.url_for",
                    return_value="http://example.com/reset/token",
                ):
                    from server.config.mails import send_password_reset_email

                    send_password_reset_email(user, "dummy_token")

        mock_task.delay.assert_called_once()
        args, kwargs = mock_task.delay.call_args
        to_arg = args[0] if args else kwargs.get("to")
        self.assertEqual("user@example.com", to_arg)

    @patch("server.config.mails.mail")
    def test_password_reset_uses_sync_send_when_async_disabled(
        self, mock_mail
    ):
        """send_password_reset_email must call mail.send directly when
        USE_ASYNC_EMAIL is False."""
        mock_mail.send = MagicMock()
        self.app.config["USE_ASYNC_EMAIL"] = False

        user = self._make_mock_user()

        with self.app.app_context():
            with self.app.test_request_context("/"):
                with patch(
                    "server.config.mails.url_for",
                    return_value="http://example.com/reset/token",
                ):
                    from server.config.mails import send_password_reset_email

                    send_password_reset_email(user, "dummy_token")

        mock_mail.send.assert_called_once()


if __name__ == "__main__":
    unittest.main()
