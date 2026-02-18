"""Tests for rate limiting on authentication endpoints (US-001)."""

import json
import unittest

from core import create_app, db

from . import BaseTestClass

# Non-existent user credentials — guaranteed to never authenticate,
# so current_user.is_authenticated stays False throughout all rate-limit tests.
_FAKE_EMAIL = "ratelimit_test_nonexistent@nowhere.invalid"
_FAKE_PASSWORD = "ImpossiblePassword!99"


class RateLimitingTestCase(BaseTestClass):
    """Test suite for rate limiting behaviour on /login and /signup."""

    __SKIP_ALL__: bool = False

    def _fresh_client(self):
        """Return a new test client with an isolated cookie jar."""
        return self.app.test_client()

    def _reset_limiter(self):
        """Reset all in-memory rate-limit counters (requires app context)."""
        with self.app.app_context():
            from core import limiter

            limiter.reset()

    def _override_limit(self, key: str, value: str):
        """Override a rate-limit config value and return the original."""
        with self.app.app_context():
            original = self.app.config.get(key)
            self.app.config[key] = value
        return original

    def _restore_limit(self, key: str, value):
        """Restore a rate-limit config value to its original."""
        with self.app.app_context():
            self.app.config[key] = value

    # ---------------------------------------------------------------
    # /login rate limiting tests
    # ---------------------------------------------------------------

    @unittest.skipIf(__SKIP_ALL__, "Deactivate to run latest created test.")
    def test_login_under_rate_limit_succeeds(self):
        """Requests below the threshold should return a non-429 status."""
        client = self._fresh_client()
        self._reset_limiter()
        for _ in range(3):
            res = client.post(
                "/login",
                json={"email": _FAKE_EMAIL, "password": _FAKE_PASSWORD},
            )
            self.assertNotEqual(
                429,
                res.status_code,
                "Expected non-429 for requests under the threshold.",
            )

    @unittest.skipIf(__SKIP_ALL__, "Deactivate to run latest created test.")
    def test_login_exceeds_rate_limit_returns_429(self):
        """After exceeding RATE_LIMIT_LOGIN threshold, a 429 must be returned."""
        original = self._override_limit("RATE_LIMIT_LOGIN", "2/minute")
        client = self._fresh_client()
        self._reset_limiter()

        responses = []
        for _ in range(4):
            responses.append(
                client.post(
                    "/login",
                    json={"email": _FAKE_EMAIL, "password": _FAKE_PASSWORD},
                )
            )

        self._restore_limit("RATE_LIMIT_LOGIN", original)
        status_codes = [r.status_code for r in responses]
        self.assertIn(
            429,
            status_codes,
            f"Expected at least one 429 response but got: {status_codes}",
        )

    @unittest.skipIf(__SKIP_ALL__, "Deactivate to run latest created test.")
    def test_login_429_response_has_correct_structure(self):
        """A 429 response body must contain 'message' and 'status' keys."""
        original = self._override_limit("RATE_LIMIT_LOGIN", "1/minute")
        client = self._fresh_client()
        self._reset_limiter()

        client.post(
            "/login", json={"email": _FAKE_EMAIL, "password": _FAKE_PASSWORD}
        )
        res = client.post(
            "/login", json={"email": _FAKE_EMAIL, "password": _FAKE_PASSWORD}
        )
        self._restore_limit("RATE_LIMIT_LOGIN", original)

        self.assertEqual(429, res.status_code)
        data = json.loads(res.data)
        self.assertIn("message", data)
        self.assertIn("status", data)
        self.assertEqual(429, data["status"])

    @unittest.skipIf(__SKIP_ALL__, "Deactivate to run latest created test.")
    def test_login_429_response_has_retry_after_header(self):
        """A 429 response must include the Retry-After header."""
        original = self._override_limit("RATE_LIMIT_LOGIN", "1/minute")
        client = self._fresh_client()
        self._reset_limiter()

        client.post(
            "/login", json={"email": _FAKE_EMAIL, "password": _FAKE_PASSWORD}
        )
        res = client.post(
            "/login", json={"email": _FAKE_EMAIL, "password": _FAKE_PASSWORD}
        )
        self._restore_limit("RATE_LIMIT_LOGIN", original)

        self.assertEqual(429, res.status_code)
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
        client = self._fresh_client()
        self._reset_limiter()
        for i in range(2):
            res = client.post(
                "/signup",
                json={
                    "username": f"ratelimituser{i}",
                    "role": "Guest",
                    "email": f"ratelimit{i}@nowhere.invalid",
                    "password": "ImpossiblePassword!99",
                },
            )
            self.assertNotEqual(
                429,
                res.status_code,
                "Expected non-429 for requests under the threshold.",
            )

    @unittest.skipIf(__SKIP_ALL__, "Deactivate to run latest created test.")
    def test_signup_exceeds_rate_limit_returns_429(self):
        """After exceeding RATE_LIMIT_SIGNUP threshold a 429 must be returned."""
        original = self._override_limit("RATE_LIMIT_SIGNUP", "2/minute")
        client = self._fresh_client()
        self._reset_limiter()

        responses = []
        for i in range(4):
            responses.append(
                client.post(
                    "/signup",
                    json={
                        "username": f"ratelimituser{i}",
                        "role": "Guest",
                        "email": f"ratelimit{i}@nowhere.invalid",
                        "password": "ImpossiblePassword!99",
                    },
                )
            )

        self._restore_limit("RATE_LIMIT_SIGNUP", original)
        status_codes = [r.status_code for r in responses]
        self.assertIn(
            429,
            status_codes,
            f"Expected at least one 429 response but got: {status_codes}",
        )

    @unittest.skipIf(__SKIP_ALL__, "Deactivate to run latest created test.")
    def test_signup_429_response_has_correct_structure(self):
        """A 429 signup response body must contain 'message' and 'status'."""
        original = self._override_limit("RATE_LIMIT_SIGNUP", "1/minute")
        client = self._fresh_client()
        self._reset_limiter()

        client.post(
            "/signup",
            json={
                "username": "ratelimitusera",
                "role": "Guest",
                "email": "ratelimita@nowhere.invalid",
                "password": "ImpossiblePassword!99",
            },
        )
        res = client.post(
            "/signup",
            json={
                "username": "ratelimituserb",
                "role": "Guest",
                "email": "ratelimitb@nowhere.invalid",
                "password": "ImpossiblePassword!99",
            },
        )
        self._restore_limit("RATE_LIMIT_SIGNUP", original)

        self.assertEqual(429, res.status_code)
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
