"""Test suite for asynchronous email task dispatch and failure handling.

Test coverage (TASK-015-7)
--------------------------
 1.  Signup route dispatches ``send_email_task.delay`` (called once).
 2.  ``USE_ASYNC_EMAIL=False`` — signup does *not* dispatch the task.
 3.  ``send_email_task`` succeeds when ``mail.send`` works.
 4.  HTTP 200 is returned before email delivery completes.
 5.  ``send_email_task`` retries on SMTP failure (expected exception raised).
 6.  ``send_email_task`` retries exactly ``max_retries`` times before failing.
 7.  ``send_email_task`` re-raises the exception on permanent failure.
 8.  Password-reset helper dispatches ``send_email_task.delay`` when async.
 9.  Password-reset helper falls back to synchronous send when not async.
10.  Signup response contains the expected ``user`` and ``jwt`` keys.

Config notes (config/testing.py)
----------------------------------
* ``CELERY_TASK_ALWAYS_EAGER = True``   — tasks execute synchronously.
* ``CELERY_TASK_EAGER_PROPAGATES = True`` — exceptions propagate to tests.
* ``USE_ASYNC_EMAIL = False``            — email dispatch off by default.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

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
# 3, 5, 6, 7 — send_email_task unit tests
# ---------------------------------------------------------------------------


class TestSendEmailTask(BaseTestClass):
    """Unit tests that exercise send_email_task directly via .apply()."""

    def _apply_task(self, **overrides):
        """Run the task synchronously and return the AsyncResult."""
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

    @patch(_MAIL_PATH)
    def test_task_retries_on_smtp_failure(self, mock_mail):
        """Task must raise an exception when mail.send fails."""
        mock_mail.send.side_effect = ConnectionError("SMTP unreachable")

        with self.assertRaises(Exception):
            self._apply_task()

    @patch(_MAIL_PATH)
    def test_task_retries_exactly_max_retries_times(self, mock_mail):
        """mail.send must be called 1 + max_retries (=4) times total,
        verifying retry exhaustion.

        ``CELERY_TASK_EAGER_PROPAGATES`` is temporarily disabled so that
        Celery's eager runner executes the task the full retry cycle instead
        of propagating ``Retry`` on the first attempt.
        """
        from core.tasks import celery
        from core.tasks.email_tasks import send_email_task

        mock_mail.send.side_effect = OSError("Persistent SMTP failure")

        celery.conf.update(task_eager_propagates=False)
        try:
            # apply() without throw=True so task_eager_propagates=False takes effect
            result = send_email_task.apply(kwargs=_VALID_EMAIL_KWARGS)
        finally:
            celery.conf.update(task_eager_propagates=True)

        self.assertTrue(result.failed())
        self.assertEqual(
            1 + send_email_task.max_retries,
            mock_mail.send.call_count,
        )

    @patch(_MAIL_PATH)
    def test_task_re_raises_exception_on_permanent_failure(self, mock_mail):
        """After exhausting all retries the original exception type is stored
        in the result.

        ``CELERY_TASK_EAGER_PROPAGATES`` is temporarily disabled so that
        Celery runs the full retry cycle; the original ``RuntimeError`` is
        wrapped in ``result.info`` after ``max_retries`` are exhausted.
        """
        from core.tasks import celery
        from core.tasks.email_tasks import send_email_task

        mock_mail.send.side_effect = RuntimeError("Unrecoverable SMTP error")

        celery.conf.update(task_eager_propagates=False)
        try:
            result = send_email_task.apply(kwargs=_VALID_EMAIL_KWARGS)
        finally:
            celery.conf.update(task_eager_propagates=True)

        self.assertTrue(result.failed())
        self.assertIsInstance(result.info, RuntimeError)

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
