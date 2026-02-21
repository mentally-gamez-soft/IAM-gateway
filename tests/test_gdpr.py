"""Test suite for US-012 — GDPR compliance endpoints.

Covers:
    - TASK-012-1: GET/POST /user/data (data export)
    - TASK-012-2: DELETE /user/account (soft-delete + anonymize)
    - TASK-012-3: GET/POST /user/consent and PUT /user/consent
    - TASK-012-4: Blocked access for deleted accounts
"""

import json
import unittest

from core import db
from core.users.models import GwUser, UserConsent

from . import BaseTestClass


class GdprTestCase(BaseTestClass):
    """Test cases for GDPR compliance endpoints (US-012)."""

    __SKIP_ALL__: bool = False
    __DATA_EXPORT_TESTS__: bool = True
    __DELETE_ACCOUNT_TESTS__: bool = True
    __CONSENT_TESTS__: bool = True

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _login_active_user(self):
        """Login as guest_active and return (response, parsed_data)."""
        res = self.login("guest_active@xyz.com", "2222")
        data = json.loads(res.data)
        return res, data

    def _build_auth_payload(self, login_data: dict) -> dict:
        """Build a minimal auth payload from login response data.

        Args:
            login_data (dict): Parsed JSON body returned by login endpoint.

        Returns:
            dict: Payload containing the data sub-object.
        """
        return {"data": login_data["data"]}

    def _build_extended_payload(self, login_data: dict, extra: dict) -> dict:
        """Build an auth payload with additional fields merged into data.

        Args:
            login_data (dict): Parsed JSON body returned by login endpoint.
            extra (dict): Extra keys/values to merge into data.

        Returns:
            dict: Extended payload.
        """
        return {"data": {**login_data["data"], **extra}}

    def _get_active_user_id(self):
        """Return the ID of guest_active from the database.

        Returns:
            UUID: The user ID.
        """
        with self.app.app_context():
            user = GwUser.query.filter_by(email="guest_active@xyz.com").first()
            return user.id

    # -----------------------------------------------------------------------
    # TASK-012-1 — GET /user/data (data export)
    # -----------------------------------------------------------------------

    @unittest.skipIf(__SKIP_ALL__, "Disabled.")
    @unittest.skipUnless(
        __DATA_EXPORT_TESTS__, "Family of tests for data export endpoint."
    )
    def test_data_export_unauthenticated_returns_401(self):
        """POST /user/data returns 401 when the token is invalid."""
        payload = {
            "data": {"user": "invalid", "access_token": "bad.token.here"}
        }
        res = self.client.post("/user/data", json=payload)

        self.assertEqual(401, res.status_code)

    @unittest.skipIf(__SKIP_ALL__, "Disabled.")
    @unittest.skipUnless(
        __DATA_EXPORT_TESTS__, "Family of tests for data export endpoint."
    )
    def test_data_export_authenticated_returns_user_data(self):
        """POST /user/data returns 200 with full personal data for authenticated user."""
        _, login_data = self._login_active_user()
        payload = self._build_auth_payload(login_data)

        res = self.client.post("/user/data", json=payload)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertIn("data", data)
        self.assertIn("account", data["data"])
        self.assertIn("roles", data["data"])
        self.assertIn("consents", data["data"])
        self.assertIn("export_metadata", data["data"])
        self.assertIn("email", data["data"]["account"])
        self.assertIn("username", data["data"]["account"])

    # -----------------------------------------------------------------------
    # TASK-012-2 — DELETE /user/account (soft-delete + anonymize)
    # -----------------------------------------------------------------------

    @unittest.skipIf(__SKIP_ALL__, "Disabled.")
    @unittest.skipUnless(
        __DELETE_ACCOUNT_TESTS__,
        "Family of tests for account deletion endpoint.",
    )
    def test_delete_account_without_confirm_returns_400(self):
        """DELETE /user/account returns 400 when confirm flag is False."""
        _, login_data = self._login_active_user()
        payload = self._build_extended_payload(
            login_data, {"confirm": False, "password": "2222"}
        )

        res = self.client.delete("/user/account", json=payload)
        data = json.loads(res.data)

        self.assertEqual(400, res.status_code)
        self.assertEqual(400, data.get("status"))

    @unittest.skipIf(__SKIP_ALL__, "Disabled.")
    @unittest.skipUnless(
        __DELETE_ACCOUNT_TESTS__,
        "Family of tests for account deletion endpoint.",
    )
    def test_delete_account_missing_confirm_returns_400(self):
        """DELETE /user/account returns 400 when confirm key is absent."""
        _, login_data = self._login_active_user()
        payload = self._build_extended_payload(
            login_data, {"password": "2222"}
        )

        res = self.client.delete("/user/account", json=payload)

        self.assertEqual(400, res.status_code)

    @unittest.skipIf(__SKIP_ALL__, "Disabled.")
    @unittest.skipUnless(
        __DELETE_ACCOUNT_TESTS__,
        "Family of tests for account deletion endpoint.",
    )
    def test_delete_account_wrong_password_returns_401(self):
        """DELETE /user/account returns 401 when the given password is incorrect."""
        _, login_data = self._login_active_user()
        payload = self._build_extended_payload(
            login_data, {"confirm": True, "password": "wrongpassword"}
        )

        res = self.client.delete("/user/account", json=payload)

        self.assertEqual(401, res.status_code)

    @unittest.skipIf(__SKIP_ALL__, "Disabled.")
    @unittest.skipUnless(
        __DELETE_ACCOUNT_TESTS__,
        "Family of tests for account deletion endpoint.",
    )
    def test_delete_account_success_returns_200(self):
        """DELETE /user/account returns 200 with correct confirm and password."""
        _, login_data = self._login_active_user()
        payload = self._build_extended_payload(
            login_data, {"confirm": True, "password": "2222"}
        )

        res = self.client.delete("/user/account", json=payload)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertEqual(200, data.get("status"))

    @unittest.skipIf(__SKIP_ALL__, "Disabled.")
    @unittest.skipUnless(
        __DELETE_ACCOUNT_TESTS__,
        "Family of tests for account deletion endpoint.",
    )
    def test_delete_account_soft_deletes_user_in_db(self):
        """After DELETE /user/account, the user is marked deleted in the database."""
        user_id = self._get_active_user_id()
        _, login_data = self._login_active_user()
        payload = self._build_extended_payload(
            login_data, {"confirm": True, "password": "2222"}
        )

        self.client.delete("/user/account", json=payload)

        with self.app.app_context():
            user = GwUser.query.filter_by(id=user_id).first()
            self.assertIsNotNone(user)
            self.assertTrue(user.deleted)
            self.assertIsNotNone(user.deleted_at)
            self.assertFalse(user.active)

    @unittest.skipIf(__SKIP_ALL__, "Disabled.")
    @unittest.skipUnless(
        __DELETE_ACCOUNT_TESTS__,
        "Family of tests for account deletion endpoint.",
    )
    def test_delete_account_anonymizes_email_and_username(self):
        """After DELETE /user/account, user email and username are anonymized."""
        user_id = self._get_active_user_id()
        _, login_data = self._login_active_user()
        payload = self._build_extended_payload(
            login_data, {"confirm": True, "password": "2222"}
        )

        self.client.delete("/user/account", json=payload)

        with self.app.app_context():
            user = GwUser.query.filter_by(id=user_id).first()
            self.assertNotEqual("guest_active@xyz.com", user.email)
            self.assertTrue(user.email.endswith("@deleted.invalid"))
            self.assertTrue(user.username.startswith("deleted_"))

    @unittest.skipIf(__SKIP_ALL__, "Disabled.")
    @unittest.skipUnless(
        __DELETE_ACCOUNT_TESTS__,
        "Family of tests for account deletion endpoint.",
    )
    def test_second_delete_attempt_returns_error(self):
        """A second DELETE /user/account attempt is rejected (401 or 409)."""
        _, login_data = self._login_active_user()
        payload = self._build_extended_payload(
            login_data, {"confirm": True, "password": "2222"}
        )

        # First deletion succeeds
        res1 = self.client.delete("/user/account", json=payload)
        self.assertEqual(200, res1.status_code)

        # Second attempt: auth_guard blocks the deleted user (401)
        res2 = self.client.delete("/user/account", json=payload)
        self.assertIn(res2.status_code, [401, 409])

    # -----------------------------------------------------------------------
    # TASK-012-4 — Deleted user access is blocked
    # -----------------------------------------------------------------------

    @unittest.skipIf(__SKIP_ALL__, "Disabled.")
    @unittest.skipUnless(
        __DELETE_ACCOUNT_TESTS__,
        "Family of tests for deleted user access control.",
    )
    def test_deleted_user_cannot_login(self):
        """Login endpoint returns 401 or 403 for a user flagged as deleted."""
        with self.app.app_context():
            user = GwUser.query.filter_by(email="guest_active@xyz.com").first()
            user.deleted = True
            db.session.commit()

        res = self.login("guest_active@xyz.com", "2222")

        self.assertIn(res.status_code, [401, 403])

    @unittest.skipIf(__SKIP_ALL__, "Disabled.")
    @unittest.skipUnless(
        __DELETE_ACCOUNT_TESTS__,
        "Family of tests for deleted user access control.",
    )
    def test_deleted_user_jwt_rejected_by_auth_guard(self):
        """An existing JWT token returns 401 from auth_guard after the account is deleted."""
        _, login_data = self._login_active_user()
        payload = self._build_auth_payload(login_data)

        # Manually mark user as deleted (without anonymizing so the token still resolves)
        with self.app.app_context():
            user = GwUser.query.filter_by(email="guest_active@xyz.com").first()
            user.deleted = True
            db.session.commit()

        # Any auth-guarded endpoint should now return 401
        res = self.client.post("/user/data", json=payload)

        self.assertEqual(401, res.status_code)

    # -----------------------------------------------------------------------
    # TASK-012-3 — GET /user/consent
    # -----------------------------------------------------------------------

    @unittest.skipIf(__SKIP_ALL__, "Disabled.")
    @unittest.skipUnless(
        __CONSENT_TESTS__, "Family of tests for consent retrieval endpoint."
    )
    def test_get_consent_unauthenticated_returns_401(self):
        """POST /user/consent returns 401 for an invalid token."""
        payload = {
            "data": {"user": "invalid", "access_token": "bad.token.here"}
        }
        res = self.client.post("/user/consent", json=payload)

        self.assertEqual(401, res.status_code)

    @unittest.skipIf(__SKIP_ALL__, "Disabled.")
    @unittest.skipUnless(
        __CONSENT_TESTS__, "Family of tests for consent retrieval endpoint."
    )
    def test_get_consent_authenticated_returns_200(self):
        """POST /user/consent returns 200 with consent structure for authenticated user."""
        _, login_data = self._login_active_user()
        payload = self._build_auth_payload(login_data)

        res = self.client.post("/user/consent", json=payload)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertIn("data", data)
        self.assertIn("consent_given", data["data"])
        self.assertIn("consents", data["data"])
        self.assertIsInstance(data["data"]["consents"], list)

    # -----------------------------------------------------------------------
    # TASK-012-3 — PUT /user/consent
    # -----------------------------------------------------------------------

    @unittest.skipIf(__SKIP_ALL__, "Disabled.")
    @unittest.skipUnless(
        __CONSENT_TESTS__, "Family of tests for consent update endpoint."
    )
    def test_update_consent_missing_consent_given_returns_400(self):
        """PUT /user/consent returns 400 when consent_given is not provided."""
        _, login_data = self._login_active_user()
        # deliberately omit consent_given
        payload = self._build_auth_payload(login_data)

        res = self.client.put("/user/consent", json=payload)

        self.assertEqual(400, res.status_code)

    @unittest.skipIf(__SKIP_ALL__, "Disabled.")
    @unittest.skipUnless(
        __CONSENT_TESTS__, "Family of tests for consent update endpoint."
    )
    def test_update_consent_granted_true_returns_200(self):
        """PUT /user/consent returns 200 when granting consent."""
        _, login_data = self._login_active_user()
        payload = self._build_extended_payload(
            login_data, {"consent_given": True}
        )

        res = self.client.put("/user/consent", json=payload)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIn("data", data)
        self.assertTrue(data["data"]["consent_given"])

    @unittest.skipIf(__SKIP_ALL__, "Disabled.")
    @unittest.skipUnless(
        __CONSENT_TESTS__, "Family of tests for consent update endpoint."
    )
    def test_update_consent_tracks_consent_at_timestamp(self):
        """PUT /user/consent sets a non-null consent_at timestamp after update."""
        _, login_data = self._login_active_user()
        payload = self._build_extended_payload(
            login_data, {"consent_given": True}
        )

        res = self.client.put("/user/consent", json=payload)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIsNotNone(data["data"]["consent_at"])

    @unittest.skipIf(__SKIP_ALL__, "Disabled.")
    @unittest.skipUnless(
        __CONSENT_TESTS__, "Family of tests for consent update endpoint."
    )
    def test_update_consent_revoke_sets_revoked_at(self):
        """PUT /user/consent with granted=False sets revoked_at on the consent record."""
        user_id = self._get_active_user_id()
        _, login_data = self._login_active_user()

        # Grant per-type consent
        payload_grant = self._build_extended_payload(
            login_data,
            {
                "consent_given": True,
                "consents": [{"consent_type": "marketing", "granted": True}],
            },
        )
        self.client.put("/user/consent", json=payload_grant)

        # Revoke per-type consent using same token (JWT still valid)
        payload_revoke = self._build_extended_payload(
            login_data,
            {
                "consent_given": False,
                "consents": [{"consent_type": "marketing", "granted": False}],
            },
        )
        res = self.client.put("/user/consent", json=payload_revoke)
        self.assertEqual(200, res.status_code)

        with self.app.app_context():
            records = UserConsent.get_all_for_user(user_id)
            marketing = next(
                (r for r in records if r.consent_type == "marketing"), None
            )
            self.assertIsNotNone(marketing)
            self.assertFalse(marketing.granted)
            self.assertIsNotNone(marketing.revoked_at)

    @unittest.skipIf(__SKIP_ALL__, "Disabled.")
    @unittest.skipUnless(
        __CONSENT_TESTS__, "Family of tests for consent update endpoint."
    )
    def test_update_consent_creates_per_type_records(self):
        """PUT /user/consent with consents list creates UserConsent rows in the DB."""
        user_id = self._get_active_user_id()
        _, login_data = self._login_active_user()
        payload = self._build_extended_payload(
            login_data,
            {
                "consent_given": True,
                "consents": [
                    {"consent_type": "marketing", "granted": True},
                    {"consent_type": "analytics", "granted": False},
                ],
            },
        )

        res = self.client.put("/user/consent", json=payload)
        self.assertEqual(200, res.status_code)

        with self.app.app_context():
            records = UserConsent.get_all_for_user(user_id)
            consent_types = {r.consent_type for r in records}
            self.assertIn("marketing", consent_types)
            self.assertIn("analytics", consent_types)

    @unittest.skipIf(__SKIP_ALL__, "Disabled.")
    @unittest.skipUnless(
        __CONSENT_TESTS__, "Family of tests for consent update endpoint."
    )
    def test_get_consent_reflects_updated_preferences(self):
        """GET /user/consent returns the latest values after a PUT /user/consent."""
        _, login_data = self._login_active_user()

        # Update consent
        payload_put = self._build_extended_payload(
            login_data, {"consent_given": True}
        )
        self.client.put("/user/consent", json=payload_put)

        # Read consent back with same token
        payload_get = self._build_auth_payload(login_data)
        res = self.client.post("/user/consent", json=payload_get)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertTrue(data["data"]["consent_given"])


if __name__ == "__main__":
    unittest.main()
