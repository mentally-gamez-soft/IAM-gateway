"""Tests for the user profile management endpoints (US-011).

Covers:
    GET  /profile   — retrieve authenticated user's profile
    PUT  /profile   — update mutable profile fields

At least 10 test cases per task specification TASK-011-5.
"""

import json
import unittest

from . import BaseTestClass


class ProfileTestCase(BaseTestClass):
    """Test suite for US-011 profile endpoints."""

    __SKIP_ALL__: bool = False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _login_active_user(self):
        """Log in as the active user and return the full response data."""
        res = self.login("guest_active@xyz.com", "2222")
        self.assertEqual(200, res.status_code)
        return json.loads(res.data)

    def _build_get_profile_payload(self, login_data: dict) -> dict:
        """Build the payload for GET /profile using login response data."""
        return {
            "data": {
                "access_token": login_data["data"]["access_token"],
                "user": login_data["data"]["user"],
            }
        }

    def _build_put_profile_payload(
        self, login_data: dict, profile_fields: dict
    ) -> dict:
        """Build the payload for PUT /profile."""
        return {
            "data": {
                "access_token": login_data["data"]["access_token"],
                "user": login_data["data"]["user"],
                "profile": profile_fields,
            }
        }

    # ------------------------------------------------------------------
    # GET /profile — happy path
    # ------------------------------------------------------------------

    @unittest.skipIf(__SKIP_ALL__, "Skip all")
    def test_get_profile_returns_200_for_authenticated_user(self):
        """GET /profile returns HTTP 200 and profile data for a logged-in user."""
        login_data = self._login_active_user()
        payload = self._build_get_profile_payload(login_data)

        res = self.client.get("/profile", json=payload)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIn("profile", data["data"])

    @unittest.skipIf(__SKIP_ALL__, "Skip all")
    def test_get_profile_contains_expected_fields(self):
        """GET /profile response includes all expected profile fields."""
        login_data = self._login_active_user()
        payload = self._build_get_profile_payload(login_data)

        res = self.client.get("/profile", json=payload)
        data = json.loads(res.data)
        profile = data["data"]["profile"]

        for field in (
            "id",
            "username",
            "email",
            "display_name",
            "avatar_url",
            "bio",
            "language_preference",
            "timezone",
            "is_admin",
            "active",
            "created_on",
            "roles",
        ):
            self.assertIn(
                field,
                profile,
                msg=f"Expected field '{field}' missing from profile response.",
            )

    @unittest.skipIf(__SKIP_ALL__, "Skip all")
    def test_get_profile_default_language_is_en(self):
        """GET /profile returns 'en' as the default language_preference."""
        login_data = self._login_active_user()
        payload = self._build_get_profile_payload(login_data)

        res = self.client.get("/profile", json=payload)
        data = json.loads(res.data)
        profile = data["data"]["profile"]

        self.assertEqual("en", profile["language_preference"])

    @unittest.skipIf(__SKIP_ALL__, "Skip all")
    def test_get_profile_default_timezone_is_utc(self):
        """GET /profile returns 'UTC' as the default timezone."""
        login_data = self._login_active_user()
        payload = self._build_get_profile_payload(login_data)

        res = self.client.get("/profile", json=payload)
        data = json.loads(res.data)
        profile = data["data"]["profile"]

        self.assertEqual("UTC", profile["timezone"])

    # ------------------------------------------------------------------
    # GET /profile — authentication enforcement
    # ------------------------------------------------------------------

    @unittest.skipIf(__SKIP_ALL__, "Skip all")
    def test_get_profile_returns_401_for_unauthenticated_request(self):
        """GET /profile returns HTTP 401 when no JWT is supplied."""
        # Completely missing data
        res = self.client.get("/profile", json={})
        self.assertEqual(401, res.status_code)

    @unittest.skipIf(__SKIP_ALL__, "Skip all")
    def test_get_profile_returns_401_with_invalid_jwt(self):
        """GET /profile returns HTTP 401 when the JWT is tampered."""
        payload = {"data": {"jwt": "invalid.jwt.token", "user": "fakeuser=="}}
        res = self.client.get("/profile", json=payload)
        self.assertIn(res.status_code, (401, 422))

    # ------------------------------------------------------------------
    # PUT /profile — happy path
    # ------------------------------------------------------------------

    @unittest.skipIf(__SKIP_ALL__, "Skip all")
    def test_put_profile_updates_display_name(self):
        """PUT /profile successfully updates display_name."""
        login_data = self._login_active_user()
        payload = self._build_put_profile_payload(
            login_data, {"display_name": "My Display Name"}
        )

        res = self.client.put("/profile", json=payload)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertEqual(
            "My Display Name", data["data"]["profile"]["display_name"]
        )

    @unittest.skipIf(__SKIP_ALL__, "Skip all")
    def test_put_profile_updates_multiple_fields_at_once(self):
        """PUT /profile can update several fields in a single request."""
        login_data = self._login_active_user()
        payload = self._build_put_profile_payload(
            login_data,
            {
                "display_name": "Multifield User",
                "language_preference": "fr",
                "timezone": "Europe/Paris",
                "bio": "This is my bio.",
            },
        )

        res = self.client.put("/profile", json=payload)
        data = json.loads(res.data)
        profile = data["data"]["profile"]

        self.assertEqual(200, res.status_code)
        self.assertEqual("Multifield User", profile["display_name"])
        self.assertEqual("fr", profile["language_preference"])
        self.assertEqual("Europe/Paris", profile["timezone"])
        self.assertEqual("This is my bio.", profile["bio"])

    @unittest.skipIf(__SKIP_ALL__, "Skip all")
    def test_put_profile_sets_profile_updated_at(self):
        """PUT /profile sets the profile_updated_at timestamp."""
        login_data = self._login_active_user()
        payload = self._build_put_profile_payload(
            login_data, {"display_name": "Timestamp Test"}
        )

        res = self.client.put("/profile", json=payload)
        data = json.loads(res.data)
        profile = data["data"]["profile"]

        self.assertEqual(200, res.status_code)
        self.assertIsNotNone(
            profile.get("profile_updated_at"),
            "profile_updated_at should be set after a PUT /profile call.",
        )

    @unittest.skipIf(__SKIP_ALL__, "Skip all")
    def test_put_profile_with_empty_profile_body_returns_current_profile(self):
        """PUT /profile with an empty profile dict returns the current profile (no error)."""
        login_data = self._login_active_user()
        payload = self._build_put_profile_payload(login_data, {})

        res = self.client.put("/profile", json=payload)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIn("profile", data["data"])

    @unittest.skipIf(__SKIP_ALL__, "Skip all")
    def test_put_profile_updates_avatar_url(self):
        """PUT /profile can set avatar_url."""
        login_data = self._login_active_user()
        avatar = "https://example.com/avatar.png"
        payload = self._build_put_profile_payload(
            login_data, {"avatar_url": avatar}
        )

        res = self.client.put("/profile", json=payload)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertEqual(avatar, data["data"]["profile"]["avatar_url"])

    # ------------------------------------------------------------------
    # PUT /profile — validation: protected fields must be rejected
    # ------------------------------------------------------------------

    @unittest.skipIf(__SKIP_ALL__, "Skip all")
    def test_put_profile_rejects_email_update(self):
        """PUT /profile returns 400 when client attempts to change email."""
        login_data = self._login_active_user()
        payload = self._build_put_profile_payload(
            login_data, {"email": "hacker@evil.com"}
        )

        res = self.client.put("/profile", json=payload)
        data = json.loads(res.data)

        self.assertEqual(400, res.status_code)
        self.assertIn("Protected", data["message"])

    @unittest.skipIf(__SKIP_ALL__, "Skip all")
    def test_put_profile_rejects_username_update(self):
        """PUT /profile returns 400 when client attempts to change username."""
        login_data = self._login_active_user()
        payload = self._build_put_profile_payload(
            login_data, {"username": "hacked_username"}
        )

        res = self.client.put("/profile", json=payload)
        data = json.loads(res.data)

        self.assertEqual(400, res.status_code)
        self.assertIn("Protected", data["message"])

    @unittest.skipIf(__SKIP_ALL__, "Skip all")
    def test_put_profile_rejects_role_update(self):
        """PUT /profile returns 400 when client attempts to change roles."""
        login_data = self._login_active_user()
        payload = self._build_put_profile_payload(
            login_data, {"roles": ["admin"]}
        )

        res = self.client.put("/profile", json=payload)
        data = json.loads(res.data)

        self.assertEqual(400, res.status_code)
        self.assertIn("Protected", data["message"])

    # ------------------------------------------------------------------
    # PUT /profile — validation: field constraints
    # ------------------------------------------------------------------

    @unittest.skipIf(__SKIP_ALL__, "Skip all")
    def test_put_profile_rejects_invalid_language_preference(self):
        """PUT /profile returns 400 for a single-char language_preference."""
        login_data = self._login_active_user()
        payload = self._build_put_profile_payload(
            login_data, {"language_preference": "x"}  # too short — must be 2-5
        )

        res = self.client.put("/profile", json=payload)
        data = json.loads(res.data)

        self.assertEqual(400, res.status_code)
        self.assertIn("language_preference", data["message"])

    @unittest.skipIf(__SKIP_ALL__, "Skip all")
    def test_put_profile_rejects_too_long_display_name(self):
        """PUT /profile returns 400 when display_name exceeds 80 characters."""
        login_data = self._login_active_user()
        long_name = "A" * 81
        payload = self._build_put_profile_payload(
            login_data, {"display_name": long_name}
        )

        res = self.client.put("/profile", json=payload)
        data = json.loads(res.data)

        self.assertEqual(400, res.status_code)
        self.assertIn("display_name", data["message"])

    @unittest.skipIf(__SKIP_ALL__, "Skip all")
    def test_put_profile_rejects_too_long_avatar_url(self):
        """PUT /profile returns 400 when avatar_url exceeds 255 characters."""
        login_data = self._login_active_user()
        long_url = "https://example.com/" + "a" * 240
        payload = self._build_put_profile_payload(
            login_data, {"avatar_url": long_url}
        )

        res = self.client.put("/profile", json=payload)
        data = json.loads(res.data)

        self.assertEqual(400, res.status_code)
        self.assertIn("avatar_url", data["message"])

    # ------------------------------------------------------------------
    # PUT /profile — authentication enforcement
    # ------------------------------------------------------------------

    @unittest.skipIf(__SKIP_ALL__, "Skip all")
    def test_put_profile_returns_401_for_unauthenticated_request(self):
        """PUT /profile returns HTTP 401 when no JWT is supplied."""
        res = self.client.put("/profile", json={})
        self.assertEqual(401, res.status_code)


if __name__ == "__main__":
    unittest.main()
