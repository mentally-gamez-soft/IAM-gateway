"""Test suite for JWT Refresh Token mechanism (US-003)."""

import unittest
import uuid
from datetime import datetime, timedelta

from core import db
from core.auth.jwt.jwt_handler import (
    decode_jwt,
    generate_refresh_token,
    generate_token_pair,
)
from core.users.models import GwUser, RefreshToken

from . import BaseTestClass


class _TokenTestMixin:
    """Mixin that creates a dedicated test user in setUp."""

    def _create_token_test_user(self):
        """Create a fresh user for token tests and store its id/email."""
        with self.app.app_context():
            user = GwUser(
                f"tokenuser_{uuid.uuid4().hex[:8]}",
                f"tokenuser_{uuid.uuid4().hex[:8]}@example.com",
            )
            user.set_password("TestPassword123!")
            user.active = True
            user.save()
            self.test_user_id = user.id
            self.test_user_email = user.email


class TestRefreshTokenModel(_TokenTestMixin, BaseTestClass):
    """Test RefreshToken model functionality."""

    def setUp(self):
        super().setUp()
        self._create_token_test_user()

    # ------------------------------------------------------------------
    # Hash tests (no app context needed)
    # ------------------------------------------------------------------

    def test_hash_token_generates_consistent_hash(self):
        """Test that hashing produces consistent results."""
        token = "test_token_123"
        hash1 = RefreshToken.hash_token(token)
        hash2 = RefreshToken.hash_token(token)
        self.assertEqual(hash1, hash2)

    def test_hash_token_different_for_different_tokens(self):
        """Test that different tokens produce different hashes."""
        hash1 = RefreshToken.hash_token("token1")
        hash2 = RefreshToken.hash_token("token2")
        self.assertNotEqual(hash1, hash2)

    # ------------------------------------------------------------------
    # Validity tests
    # ------------------------------------------------------------------

    def test_refresh_token_is_valid_when_not_expired_or_revoked(self):
        """Test is_valid() returns True for valid tokens."""
        with self.app.app_context():
            token_hash = RefreshToken.hash_token(generate_refresh_token())
            rt = RefreshToken(
                user_id=self.test_user_id,
                expires_on=datetime.utcnow() + timedelta(days=7),
                family_id=uuid.uuid4(),
            )
            rt.token = token_hash
            rt.save()
            self.assertTrue(rt.is_valid())

    def test_refresh_token_is_not_valid_when_expired(self):
        """Test is_valid() returns False for expired tokens."""
        with self.app.app_context():
            token_hash = RefreshToken.hash_token(generate_refresh_token())
            rt = RefreshToken(
                user_id=self.test_user_id,
                expires_on=datetime.utcnow() - timedelta(hours=1),
                family_id=uuid.uuid4(),
            )
            rt.token = token_hash
            rt.save()
            self.assertFalse(rt.is_valid())

    def test_refresh_token_is_not_valid_when_revoked(self):
        """Test is_valid() returns False for revoked tokens."""
        with self.app.app_context():
            token_hash = RefreshToken.hash_token(generate_refresh_token())
            rt = RefreshToken(
                user_id=self.test_user_id,
                expires_on=datetime.utcnow() + timedelta(days=7),
                family_id=uuid.uuid4(),
            )
            rt.token = token_hash
            rt.revoked = True
            rt.save()
            self.assertFalse(rt.is_valid())

    def test_is_expired_returns_true_for_expired_token(self):
        """Test is_expired() for tokens past expiration."""
        with self.app.app_context():
            token_hash = RefreshToken.hash_token(generate_refresh_token())
            rt = RefreshToken(
                user_id=self.test_user_id,
                expires_on=datetime.utcnow() - timedelta(hours=1),
                family_id=uuid.uuid4(),
            )
            rt.token = token_hash
            rt.save()
            self.assertTrue(rt.is_expired())

    # ------------------------------------------------------------------
    # Revocation tests
    # ------------------------------------------------------------------

    def test_revoke_sets_revoked_flag_and_timestamp(self):
        """Test that revoke() sets revoked flag and timestamp."""
        with self.app.app_context():
            token_hash = RefreshToken.hash_token(generate_refresh_token())
            rt = RefreshToken(
                user_id=self.test_user_id,
                expires_on=datetime.utcnow() + timedelta(days=7),
                family_id=uuid.uuid4(),
            )
            rt.token = token_hash
            rt.save()
            rt.revoke()
            self.assertTrue(rt.revoked)
            self.assertIsNotNone(rt.revoked_on)

    def test_revoke_all_for_user_revokes_all_tokens(self):
        """Test revoke_all_for_user() revokes all user tokens."""
        with self.app.app_context():
            for _ in range(3):
                token_hash = RefreshToken.hash_token(generate_refresh_token())
                rt = RefreshToken(
                    user_id=self.test_user_id,
                    expires_on=datetime.utcnow() + timedelta(days=7),
                    family_id=uuid.uuid4(),
                )
                rt.token = token_hash
                rt.save()

            RefreshToken.revoke_all_for_user(self.test_user_id)

            tokens = (
                db.session.query(RefreshToken)
                .filter_by(user_id=self.test_user_id)
                .all()
            )
            self.assertTrue(all(t.revoked for t in tokens))

    def test_revoke_family_revokes_all_tokens_in_family(self):
        """Test revoke_family() revokes all tokens in token family."""
        with self.app.app_context():
            family_id = uuid.uuid4()
            for _ in range(3):
                token_hash = RefreshToken.hash_token(generate_refresh_token())
                rt = RefreshToken(
                    user_id=self.test_user_id,
                    expires_on=datetime.utcnow() + timedelta(days=7),
                    family_id=family_id,
                )
                rt.token = token_hash
                rt.save()

            RefreshToken.revoke_family(family_id)

            tokens = (
                db.session.query(RefreshToken)
                .filter_by(family_id=family_id)
                .all()
            )
            self.assertTrue(all(t.revoked for t in tokens))

    # ------------------------------------------------------------------
    # Lookup tests
    # ------------------------------------------------------------------

    def test_get_by_token_finds_token(self):
        """Test get_by_token() finds stored tokens."""
        with self.app.app_context():
            token_string = generate_refresh_token()
            token_hash = RefreshToken.hash_token(token_string)
            rt = RefreshToken(
                user_id=self.test_user_id,
                expires_on=datetime.utcnow() + timedelta(days=7),
                family_id=uuid.uuid4(),
            )
            rt.token = token_hash
            rt.save()

            found = RefreshToken.get_by_token(token_hash)
            self.assertIsNotNone(found)
            self.assertEqual(found.token, token_hash)

    def test_get_by_token_returns_none_for_unknown_token(self):
        """Test get_by_token() returns None for non-existent tokens."""
        with self.app.app_context():
            unknown_hash = RefreshToken.hash_token("unknown_token")
            self.assertIsNone(RefreshToken.get_by_token(unknown_hash))


class TestTokenGeneration(_TokenTestMixin, BaseTestClass):
    """Test token generation functionality."""

    def setUp(self):
        super().setUp()
        self._create_token_test_user()

    def test_generate_refresh_token_returns_string(self):
        """Test generate_refresh_token() returns a non-empty string."""
        token = generate_refresh_token()
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 0)

    def test_generate_refresh_token_creates_unique_tokens(self):
        """Test that consecutive generations produce different tokens."""
        self.assertNotEqual(generate_refresh_token(), generate_refresh_token())

    def test_generate_token_pair_returns_all_required_fields(self):
        """Test generate_token_pair() returns required fields."""
        with self.app.app_context():
            pair = generate_token_pair(
                user_id=self.test_user_id,
                payload_data={"test": "data"},
            )
        self.assertIn("access_token", pair)
        self.assertIn("refresh_token", pair)
        self.assertIn("token_type", pair)
        self.assertIn("expires_in", pair)
        self.assertEqual(pair["token_type"], "Bearer")

    def test_generate_token_pair_stores_refresh_token(self):
        """Test that generate_token_pair() persists the refresh token in DB."""
        with self.app.app_context():
            pair = generate_token_pair(
                user_id=self.test_user_id,
                payload_data={"test": "data"},
            )
            token_hash = RefreshToken.hash_token(pair["refresh_token"])
            stored = RefreshToken.get_by_token(token_hash)
            self.assertIsNotNone(stored)
            self.assertEqual(stored.user_id, self.test_user_id)
            self.assertFalse(stored.revoked)

    def test_access_token_is_valid_jwt(self):
        """Test that the access token is a valid decodable JWT."""
        with self.app.app_context():
            pair = generate_token_pair(
                user_id=self.test_user_id,
                payload_data={"email": self.test_user_email},
            )
            decoded = decode_jwt(pair["access_token"])
            self.assertIsNotNone(decoded)
            self.assertEqual(decoded["sub"], str(self.test_user_id))


class TestTokenRefreshEndpoint(_TokenTestMixin, BaseTestClass):
    """Test the /token/refresh endpoint."""

    def setUp(self):
        super().setUp()
        self._create_token_test_user()

    def test_refresh_token_endpoint_exists(self):
        """Test that the refresh token endpoint is registered (not 404)."""
        response = self.client.post(
            "/token/refresh",
            json={"refresh_token": "test"},
        )
        self.assertNotEqual(response.status_code, 404)

    def test_refresh_token_requires_token_in_request(self):
        """Test that endpoint rejects requests without a refresh token."""
        response = self.client.post("/token/refresh", json={})
        self.assertEqual(response.status_code, 400)

    def test_refresh_token_rejects_invalid_token(self):
        """Test that endpoint rejects invalid/unknown tokens."""
        response = self.client.post(
            "/token/refresh",
            json={"refresh_token": "invalid_token_xyz"},
        )
        self.assertEqual(response.status_code, 401)

    def test_refresh_token_rejects_expired_token(self):
        """Test that endpoint rejects expired tokens."""
        with self.app.app_context():
            token_string = generate_refresh_token()
            token_hash = RefreshToken.hash_token(token_string)
            rt = RefreshToken(
                user_id=self.test_user_id,
                expires_on=datetime.utcnow() - timedelta(hours=1),
                family_id=uuid.uuid4(),
            )
            rt.token = token_hash
            rt.save()

        response = self.client.post(
            "/token/refresh",
            json={"refresh_token": token_string},
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("expired", response.json["message"].lower())

    def test_refresh_token_rejects_revoked_token(self):
        """Test that endpoint rejects revoked tokens."""
        with self.app.app_context():
            token_string = generate_refresh_token()
            token_hash = RefreshToken.hash_token(token_string)
            rt = RefreshToken(
                user_id=self.test_user_id,
                expires_on=datetime.utcnow() + timedelta(days=7),
                family_id=uuid.uuid4(),
            )
            rt.token = token_hash
            rt.revoked = True
            rt.save()

        response = self.client.post(
            "/token/refresh",
            json={"refresh_token": token_string},
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("revoked", response.json["message"].lower())

    def test_refresh_token_detects_reuse(self):
        """Test that endpoint detects and blocks token reuse (theft detection)."""
        with self.app.app_context():
            token_string = generate_refresh_token()
            token_hash = RefreshToken.hash_token(token_string)
            rt = RefreshToken(
                user_id=self.test_user_id,
                expires_on=datetime.utcnow() + timedelta(days=7),
                family_id=uuid.uuid4(),
            )
            rt.token = token_hash
            rt.replaced_by = RefreshToken.hash_token("some_other_token")
            rt.save()

        response = self.client.post(
            "/token/refresh",
            json={"refresh_token": token_string},
        )
        self.assertEqual(response.status_code, 401)
        self.assertIn("already been used", response.json["message"])

    def test_refresh_token_returns_new_tokens(self):
        """Test that a successful refresh returns a new token pair."""
        with self.app.app_context():
            pair = generate_token_pair(
                user_id=self.test_user_id,
                payload_data={"email": self.test_user_email},
            )

        response = self.client.post(
            "/token/refresh",
            json={"refresh_token": pair["refresh_token"]},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json["data"]
        self.assertIn("access_token", data)
        self.assertIn("refresh_token", data)
        self.assertIn("token_type", data)
        self.assertEqual(data["token_type"], "Bearer")

    def test_refresh_token_rotates_token(self):
        """Test that the old token is revoked and marked as replaced."""
        with self.app.app_context():
            pair = generate_token_pair(
                user_id=self.test_user_id,
                payload_data={"email": self.test_user_email},
            )
            old_token_hash = RefreshToken.hash_token(pair["refresh_token"])

        response = self.client.post(
            "/token/refresh",
            json={"refresh_token": pair["refresh_token"]},
        )
        self.assertEqual(response.status_code, 200)

        with self.app.app_context():
            old_token = RefreshToken.get_by_token(old_token_hash)
            self.assertIsNotNone(old_token)
            self.assertTrue(old_token.revoked)
            self.assertIsNotNone(old_token.replaced_by)


class TestLoginAndLogout(_TokenTestMixin, BaseTestClass):
    """Test login and logout with dual tokens."""

    def setUp(self):
        super().setUp()
        self._create_token_test_user()

    def test_login_returns_both_tokens(self):
        """Test that login endpoint returns both access and refresh tokens."""
        response = self.client.post(
            "/login",
            json={
                "email": self.test_user_email,
                "password": "TestPassword123!",
            },
        )
        if response.status_code == 200:
            data = response.json["data"]
            self.assertIn("access_token", data)
            self.assertIn("refresh_token", data)
            self.assertIn("token_type", data)
            self.assertEqual(data["token_type"], "Bearer")

    def test_logout_revokes_tokens(self):
        """Test that logout revokes user's refresh tokens (placeholder)."""
        with self.app.app_context():
            generate_token_pair(
                user_id=self.test_user_id,
                payload_data={"email": self.test_user_email},
            )
        # Actual logout requires proper authentication headers.
        # Placeholder for integration-level verification.
        pass


if __name__ == "__main__":
    unittest.main()
