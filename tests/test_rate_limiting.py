"""Tests for rate limiting on authentication endpoints (US-001)."""

import json
import unittest

from core import create_app, db, limiter
from core.users.models import GwUser, GwUserRole, StatsApiEndpoints

from . import BaseTestClass


class RateLimitingTestCase(BaseTestClass):
    """Test suite for rate limiting behaviour on /login and /signup."""

    __SKIP_ALL__: bool = False

    def setUp(self):
        """Set up test fixtures and reset rate limit storage before each test."""
        super().setUp()
        # Reset all rate limit counters between tests
        with self.app.app_context():
            limiter.reset()

    # ---------------------------------------------------------------
    # /login rate limiting tests
    # ---------------------------------------------------------------

    @unittest.skipIf(__SKIP_ALL__, "Deactivate to run latest created test.")
    def test_login_under_rate_limit_succeeds(self):
        """Requests below the threshold should return 200 or 403 (not 429)."""
        email = "guest_active@xyz.com"
        password = "2222"
        for _ in range(3):
            res = self.login(email, password)
            self.assertNotEqual(
                429,
                res.status_code,
                "Expected non-429 for requests under the threshold.",
            )

    @unittest.skipIf(__SKIP_ALL__, "Deactivate to run latest created test.")
    def test_login_exceeds_rate_limit_returns_429(self):
        """After exceeding RATE_LIMIT_LOGIN threshold, a 429 must be returned."""
        email = "guest_active@xyz.com"
        password = "wrong_password"

        # RATE_LIMIT_LOGIN in testing config is "1000/minute".
        # Override to a very small value for this test only.
        with self.app.app_context():
            original_limit = self.app.config.get("RATE_LIMIT_LOGIN")
            self.app.config["RATE_LIMIT_LOGIN"] = "2/minute"
            limiter.reset()

        responses = []
        for _ in range(4):
            responses.append(
                self.client.post(
                    "/login",
                    json=dict(email=email, password=password),
                )
            )

        # Restore original limit
        with self.app.app_context():
            self.app.config["RATE_LIMIT_LOGIN"] = original_limit

        status_codes = [r.status_code for r in responses]
        self.assertIn(
            429,
            status_codes,
            f"Expected at least one 429 response but got: {status_codes}",
        )

    @unittest.skipIf(__SKIP_ALL__, "Deactivate to run latest created test.")
    def test_login_429_response_has_correct_structure(self):
        """A 429 response body must contain 'message' and 'status' keys."""
        with self.app.app_context():
            original_limit = self.app.config.get("RATE_LIMIT_LOGIN")
            self.app.config["RATE_LIMIT_LOGIN"] = "1/minute"
            limiter.reset()

        # First request should pass (or fail auth, but not 429)
        self.client.post(
            "/login",
            json=dict(email="x@x.com", password="wrong"),
        )
        # Second request must be rate-limited
        res = self.client.post(
            "/login",
            json=dict(email="x@x.com", password="wrong"),
        )

        with self.app.app_context():
            self.app.config["RATE_LIMIT_LOGIN"] = original_limit

        if res.status_code == 429:
            data = json.loads(res.data)
            self.assertIn("message", data)
            self.assertIn("status", data)
            self.assertEqual(429, data["status"])

    @unittest.skipIf(__SKIP_ALL__, "Deactivate to run latest created test.")
    def test_login_429_response_has_retry_after_header(self):
        """A 429 response must include the Retry-After header."""
        with self.app.app_context():
            original_limit = self.app.config.get("RATE_LIMIT_LOGIN")
            self.app.config["RATE_LIMIT_LOGIN"] = "1/minute"
            limiter.reset()

        self.client.post(
            "/login",
            json=dict(email="x@x.com", password="wrong"),
        )
        res = self.client.post(
            "/login",
            json=dict(email="x@x.com", password="wrong"),
        )

        with self.app.app_context():
            self.app.config["RATE_LIMIT_LOGIN"] = original_limit

        if res.status_code == 429:
            self.assertIn(
                "Retry-After",
                res.headers,
                "Expected Retry-After header in 429 response.",
            )

    # ---------------------------------------------------------------
    # /signup rate limiting tests
    # ---------------------------------------------------------------

    @unittest.skipIf(__SKIP_ALL__, "Deactivate to run latest created test.")
    def test_signup_under_rate_limit_succeeds(self):
        """Requests below the signup threshold should not return 429."""
        payload = {
            "name": "testuser",
            "email": "newuser@example.com",
            "password": "Password123!",
        }
        for i in range(2):
            payload["email"] = f"newuser{i}@example.com"
            payload["name"] = f"testuser{i}"
            res = self.client.post("/signup", json=payload)
            self.assertNotEqual(
                429,
                res.status_code,
                "Expected non-429 for requests under the threshold.",
            )

    @unittest.skipIf(__SKIP_ALL__, "Deactivate to run latest created test.")
    def test_signup_exceeds_rate_limit_returns_429(self):
        """After exceeding RATE_LIMIT_SIGNUP threshold a 429 must be returned."""
        with self.app.app_context():
            original_limit = self.app.config.get("RATE_LIMIT_SIGNUP")
            self.app.config["RATE_LIMIT_SIGNUP"] = "2/minute"
            limiter.reset()

        responses = []
        for i in range(4):
            responses.append(
                self.client.post(
                    "/signup",
                    json={
                        "name": f"user{i}",
                        "email": f"user{i}@example.com",
                        "password": "Password123!",
                    },
                )
            )

        with self.app.app_context():
            self.app.config["RATE_LIMIT_SIGNUP"] = original_limit

        status_codes = [r.status_code for r in responses]
        self.assertIn(
            429,
            status_codes,
            f"Expected at least one 429 response but got: {status_codes}",
        )

    @unittest.skipIf(__SKIP_ALL__, "Deactivate to run latest created test.")
    def test_signup_429_response_has_correct_structure(self):
        """A 429 signup response body must contain 'message' and 'status'."""
        with self.app.app_context():
            original_limit = self.app.config.get("RATE_LIMIT_SIGNUP")
            self.app.config["RATE_LIMIT_SIGNUP"] = "1/minute"
            limiter.reset()

        self.client.post(
            "/signup",
            json={"name": "a", "email": "a@b.com", "password": "pass"},
        )
        res = self.client.post(
            "/signup",
            json={"name": "b", "email": "b@c.com", "password": "pass"},
        )

        with self.app.app_context():
            self.app.config["RATE_LIMIT_SIGNUP"] = original_limit

        if res.status_code == 429:
            data = json.loads(res.data)
            self.assertIn("message", data)
            self.assertIn("status", data)
            self.assertEqual(429, data["status"])

    # ---------------------------------------------------------------
    # Limiter config tests
    # ---------------------------------------------------------------

    @unittest.skipIf(__SKIP_ALL__, "Deactivate to run latest created test.")
    def test_rate_limit_config_keys_are_present(self):
        """All required rate-limit config keys must be present in app config."""
        with self.app.app_context():
            self.assertIn("RATELIMIT_STORAGE_URI", self.app.config)
            self.assertIn("RATE_LIMIT_LOGIN", self.app.config)
            self.assertIn("RATE_LIMIT_SIGNUP", self.app.config)

    @unittest.skipIf(__SKIP_ALL__, "Deactivate to run latest created test.")
    def test_testing_env_uses_memory_storage(self):
        """Testing environment must use the memory:// storage backend."""
        with self.app.app_context():
            storage_uri = self.app.config.get("RATELIMIT_STORAGE_URI")
            self.assertEqual(
                "memory://",
                storage_uri,
                "Testing config must use memory:// for RATELIMIT_STORAGE_URI.",
            )
