"""Tests for the /health and /ready endpoints (US-005).

Covers:
- Liveness probe (/health) returns 200 + correct JSON schema
- Readiness probe (/ready) returns 200 with all checks passing
- Readiness probe (/ready) returns 503 when database is unreachable
- Readiness probe (/ready) returns 503 when database raises an error
- Readiness probe includes individual check details per dependency
- Neither endpoint requires authentication or CSRF tokens
- SMTP check is skipped when APP_SEND_EMAILS is False
- Password API check behaviour when URL is configured or not
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from . import BaseTestClass


class HealthLivenessTestCase(BaseTestClass):
    """Tests for the GET /health liveness endpoint (TASK-005-1)."""

    # ── 1. Basic 200 response ───────────────────────────────────────────────

    def test_health_returns_200(self):
        """GET /health must return HTTP 200."""
        res = self.client.get("/health")
        self.assertEqual(200, res.status_code)

    # ── 2. Response schema ──────────────────────────────────────────────────

    def test_health_response_is_json(self):
        """GET /health must return a JSON response."""
        res = self.client.get("/health")
        self.assertEqual("application/json", res.content_type.split(";")[0])

    def test_health_response_has_status_field(self):
        """GET /health response must contain a 'status' field equal to 'ok'."""
        res = self.client.get("/health")
        data = json.loads(res.data)
        self.assertIn("status", data)
        self.assertEqual("ok", data["status"])

    def test_health_response_has_timestamp_field(self):
        """GET /health response must contain an ISO 8601 'timestamp' field."""
        res = self.client.get("/health")
        data = json.loads(res.data)
        self.assertIn("timestamp", data)
        self.assertIsNotNone(data["timestamp"])
        # Validate it looks like an ISO 8601 datetime string
        self.assertIn("T", data["timestamp"])

    def test_health_response_has_version_field(self):
        """GET /health response must contain a 'version' field."""
        res = self.client.get("/health")
        data = json.loads(res.data)
        self.assertIn("version", data)
        self.assertIsNotNone(data["version"])

    # ── 3. No authentication required ──────────────────────────────────────

    def test_health_does_not_require_authentication(self):
        """GET /health must be accessible without any authentication headers."""
        # Call without any JWT or session cookie
        res = self.client.get("/health")
        # Must NOT return 401 or 403
        self.assertNotEqual(401, res.status_code)
        self.assertNotEqual(403, res.status_code)
        self.assertEqual(200, res.status_code)

    # ── 4. CSRF exemption ───────────────────────────────────────────────────

    def test_health_is_callable_without_csrf_token(self):
        """GET /health must not require a CSRF token (exempt endpoint)."""
        # Explicitly ensure no CSRF-related header is sent
        res = self.client.get("/health", headers={})
        self.assertEqual(200, res.status_code)

    # ── 5. No external calls made ───────────────────────────────────────────

    @patch("core.users.routes.health.db")
    def test_health_makes_no_database_calls(self, mock_db):
        """GET /health must not query the database."""
        res = self.client.get("/health")
        self.assertEqual(200, res.status_code)
        mock_db.session.execute.assert_not_called()


class HealthReadinessTestCase(BaseTestClass):
    """Tests for the GET /ready readiness endpoint (TASK-005-2)."""

    # ── 6. Healthy scenario ─────────────────────────────────────────────────

    def test_ready_returns_200_when_db_is_available(self):
        """GET /ready must return HTTP 200 when the database is reachable.

        Uses the real SQLite test database (created in setUp).
        """
        # Silence the password_api and smtp checks — they are environment-
        # dependent and non-critical for CI.
        with (
            patch("core.users.routes.health._check_password_api") as mock_api,
            patch("core.users.routes.health._check_smtp") as mock_smtp,
        ):
            mock_api.return_value = {"status": "skipped", "detail": "mocked"}
            mock_smtp.return_value = {"status": "skipped", "detail": "mocked"}

            res = self.client.get("/ready")

        self.assertEqual(200, res.status_code)

    def test_ready_response_has_status_ready(self):
        """GET /ready body must contain status='ready' when database is up."""
        with (
            patch("core.users.routes.health._check_password_api") as mock_api,
            patch("core.users.routes.health._check_smtp") as mock_smtp,
        ):
            mock_api.return_value = {"status": "skipped", "detail": "mocked"}
            mock_smtp.return_value = {"status": "skipped", "detail": "mocked"}

            res = self.client.get("/ready")

        data = json.loads(res.data)
        self.assertEqual("ready", data["status"])

    # ── 7. Individual check results ─────────────────────────────────────────

    def test_ready_response_includes_checks_dict(self):
        """GET /ready response must include a 'checks' dictionary."""
        with (
            patch("core.users.routes.health._check_password_api") as mock_api,
            patch("core.users.routes.health._check_smtp") as mock_smtp,
        ):
            mock_api.return_value = {"status": "skipped", "detail": "mocked"}
            mock_smtp.return_value = {"status": "skipped", "detail": "mocked"}

            res = self.client.get("/ready")

        data = json.loads(res.data)
        self.assertIn("checks", data)
        self.assertIsInstance(data["checks"], dict)

    def test_ready_response_checks_has_database_key(self):
        """GET /ready checks dict must always contain a 'database' key."""
        with (
            patch("core.users.routes.health._check_password_api") as mock_api,
            patch("core.users.routes.health._check_smtp") as mock_smtp,
        ):
            mock_api.return_value = {"status": "skipped", "detail": "mocked"}
            mock_smtp.return_value = {"status": "skipped", "detail": "mocked"}

            res = self.client.get("/ready")

        data = json.loads(res.data)
        self.assertIn("database", data["checks"])

    def test_ready_database_check_is_ok_when_db_available(self):
        """GET /ready 'database' check must report 'ok' when DB is reachable."""
        with (
            patch("core.users.routes.health._check_password_api") as mock_api,
            patch("core.users.routes.health._check_smtp") as mock_smtp,
        ):
            mock_api.return_value = {"status": "skipped", "detail": "mocked"}
            mock_smtp.return_value = {"status": "skipped", "detail": "mocked"}

            res = self.client.get("/ready")

        data = json.loads(res.data)
        self.assertEqual("ok", data["checks"]["database"]["status"])

    # ── 8. Database failure scenario ────────────────────────────────────────

    def test_ready_returns_503_when_database_is_unavailable(self):
        """GET /ready must return HTTP 503 when the database is unreachable."""
        with (
            patch("core.users.routes.health.db") as mock_db,
            patch("core.users.routes.health._check_password_api") as mock_api,
            patch("core.users.routes.health._check_smtp") as mock_smtp,
        ):
            mock_db.session.execute.side_effect = Exception(
                "connection refused"
            )
            mock_api.return_value = {"status": "skipped", "detail": "mocked"}
            mock_smtp.return_value = {"status": "skipped", "detail": "mocked"}

            res = self.client.get("/ready")

        self.assertEqual(503, res.status_code)

    def test_ready_returns_not_ready_status_when_database_fails(self):
        """GET /ready body must contain status='not_ready' when database fails."""
        with (
            patch("core.users.routes.health.db") as mock_db,
            patch("core.users.routes.health._check_password_api") as mock_api,
            patch("core.users.routes.health._check_smtp") as mock_smtp,
        ):
            mock_db.session.execute.side_effect = Exception(
                "connection refused"
            )
            mock_api.return_value = {"status": "skipped", "detail": "mocked"}
            mock_smtp.return_value = {"status": "skipped", "detail": "mocked"}

            res = self.client.get("/ready")

        data = json.loads(res.data)
        self.assertEqual("not_ready", data["status"])

    def test_ready_database_check_reports_error_on_failure(self):
        """GET /ready 'database' check must report 'error' when DB is down."""
        with (
            patch("core.users.routes.health.db") as mock_db,
            patch("core.users.routes.health._check_password_api") as mock_api,
            patch("core.users.routes.health._check_smtp") as mock_smtp,
        ):
            mock_db.session.execute.side_effect = Exception(
                "connection refused"
            )
            mock_api.return_value = {"status": "skipped", "detail": "mocked"}
            mock_smtp.return_value = {"status": "skipped", "detail": "mocked"}

            res = self.client.get("/ready")

        data = json.loads(res.data)
        self.assertEqual("error", data["checks"]["database"]["status"])
        self.assertIn("detail", data["checks"]["database"])

    # ── 9. No authentication required ──────────────────────────────────────

    def test_ready_does_not_require_authentication(self):
        """GET /ready must be accessible without any authentication headers."""
        with (
            patch("core.users.routes.health._check_password_api") as mock_api,
            patch("core.users.routes.health._check_smtp") as mock_smtp,
        ):
            mock_api.return_value = {"status": "skipped", "detail": "mocked"}
            mock_smtp.return_value = {"status": "skipped", "detail": "mocked"}

            res = self.client.get("/ready")

        self.assertNotEqual(401, res.status_code)
        self.assertNotEqual(403, res.status_code)

    # ── 10. CSRF exemption ──────────────────────────────────────────────────

    def test_ready_is_callable_without_csrf_token(self):
        """GET /ready must not require a CSRF token (exempt endpoint)."""
        with (
            patch("core.users.routes.health._check_password_api") as mock_api,
            patch("core.users.routes.health._check_smtp") as mock_smtp,
        ):
            mock_api.return_value = {"status": "skipped", "detail": "mocked"}
            mock_smtp.return_value = {"status": "skipped", "detail": "mocked"}

            res = self.client.get("/ready", headers={})

        self.assertIn(res.status_code, (200, 503))

    # ── 11. SMTP skipped when disabled ─────────────────────────────────────

    def test_ready_smtp_check_is_skipped_when_send_emails_is_false(self):
        """GET /ready 'smtp' check must report 'skipped' when APP_SEND_EMAILS=False."""
        with (
            patch("core.users.routes.health._check_password_api") as mock_api,
            patch.object(
                self.app.config.__class__,
                "__getitem__",
                wraps=self.app.config.__getitem__,
            ),
        ):
            mock_api.return_value = {"status": "skipped", "detail": "mocked"}
            # Ensure email sending is disabled in this app config
            self.app.config["APP_SEND_EMAILS"] = False

            with self.app.test_client() as c:
                res = c.get("/ready")

        data = json.loads(res.data)
        self.assertIn("smtp", data["checks"])
        self.assertEqual("skipped", data["checks"]["smtp"]["status"])

    # ── 12. Password API skipped when URL unconfigured ──────────────────────

    def test_ready_password_api_check_is_skipped_when_url_not_configured(self):
        """GET /ready 'password_api' must report 'skipped' when URL is empty."""
        with patch("core.users.routes.health._check_smtp") as mock_smtp:
            mock_smtp.return_value = {"status": "skipped", "detail": "mocked"}
            original_url = self.app.config.get("WS_SCORING_PASSWORD_URL_API")
            self.app.config["WS_SCORING_PASSWORD_URL_API"] = ""

            with self.app.test_client() as c:
                res = c.get("/ready")

            self.app.config["WS_SCORING_PASSWORD_URL_API"] = original_url

        data = json.loads(res.data)
        self.assertIn("password_api", data["checks"])
        self.assertEqual("skipped", data["checks"]["password_api"]["status"])
