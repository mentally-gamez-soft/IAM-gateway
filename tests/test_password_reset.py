"""Test suite for password reset functionality."""

import json
import unittest
import uuid
from unittest.mock import patch

from config.default import (
    PASSWORD_RESET_SALT,
    PASSWORD_RESET_TOKEN_EXPIRATION,
    SECRET_KEY,
)
from core import db
from core.auth.middlewares.validation_token import generate_activation_token
from core.users.models import GwUser
from tests import BaseTestClass


class PasswordResetTestCase(BaseTestClass):
    """Test cases for password reset functionality."""

    def setUp(self):
        """Set up test fixtures."""
        # Don't call super().setUp() because it creates default users
        # Instead, create our own app context
        self.app = self.create_app_context()
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Create tables
        db.create_all()

        self._test_email = (
            f"password_reset_test_{uuid.uuid4().hex[:8]}@example.com"
        )
        self._test_username = f"password_reset_user_{uuid.uuid4().hex[:8]}"
        self._test_password = "ValidPassword123!"
        self._new_password = "NewPassword456!"

    def tearDown(self):
        """Clean up after tests."""
        # Delete test user if exists
        user = GwUser.get_by_email(self._test_email)
        if user:
            db.session.delete(user)
            db.session.commit()

        db.session.close()
        self.app_context.pop()

    def create_app_context(self):
        """Create the Flask app for testing."""
        from core import create_app

        app = create_app(settings_module="config.testing")
        return app

    def _create_test_user(self):
        """Create a test user in the database."""
        user = GwUser(username=self._test_username, email=self._test_email)
        user.set_password(self._test_password)
        user.active = True
        db.session.add(user)
        db.session.commit()
        return user

    def test_forgot_password_with_existing_email_sends_email(self):
        """Test that forgot-password endpoint sends email for existing email."""
        user = self._create_test_user()

        with patch("server.config.mails.mail.send") as mock_mail:
            response = self.client.post(
                "/forgot-password",
                data=json.dumps({"email": self._test_email}),
                content_type="application/json",
            )

            # Should return 200
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data["status"], 200)

            # Email should be sent
            mock_mail.assert_called_once()

            # Token should be stored in database
            updated_user = GwUser.get_by_email(self._test_email)
            self.assertIsNotNone(updated_user.last_password_reset_token)

    def test_forgot_password_with_nonexisting_email_returns_200(self):
        """Test that forgot-password returns 200 for non-existing email."""
        with patch("server.config.mails.mail.send") as mock_mail:
            response = self.client.post(
                "/forgot-password",
                data=json.dumps({"email": "nonexistent@example.com"}),
                content_type="application/json",
            )

            # Should return 200 (prevent enumeration)
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data["status"], 200)

            # Email should NOT be sent
            mock_mail.assert_not_called()

    def test_forgot_password_response_identical_for_existing_and_nonexisting(
        self,
    ):
        """Test that response is identical for existing and non-existing emails."""
        user = self._create_test_user()

        with patch("server.config.mails.mail.send"):
            response1 = self.client.post(
                "/forgot-password",
                data=json.dumps({"email": self._test_email}),
                content_type="application/json",
            )

        with patch("server.config.mails.mail.send"):
            response2 = self.client.post(
                "/forgot-password",
                data=json.dumps({"email": "nonexistent@example.com"}),
                content_type="application/json",
            )

        data1 = json.loads(response1.data)
        data2 = json.loads(response2.data)

        # Both responses should be identical
        self.assertEqual(data1["status"], data2["status"])
        self.assertEqual(data1["message"], data2["message"])

    def test_reset_password_with_valid_token_and_valid_password(self):
        """Test successful password reset with valid token."""
        user = self._create_test_user()

        # Generate a valid reset token
        token = generate_activation_token(
            SECRET_KEY, PASSWORD_RESET_SALT, self._test_email
        )
        user.last_password_reset_token = token
        db.session.commit()

        response = self.client.post(
            f"/reset-password/{token}",
            data=json.dumps({"password": self._new_password}),
            content_type="application/json",
        )

        # Should return 200
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], 200)

        # Password should be updated
        updated_user = GwUser.get_by_email(self._test_email)
        self.assertTrue(updated_user.check_password(self._new_password))
        self.assertFalse(updated_user.check_password(self._test_password))

        # Token should be cleared
        self.assertIsNone(updated_user.last_password_reset_token)

    def test_reset_password_with_invalid_token(self):
        """Test reset password with invalid token."""
        response = self.client.post(
            "/reset-password/invalid_token_xyz",
            data=json.dumps({"password": self._new_password}),
            content_type="application/json",
        )

        # Should return 422
        self.assertEqual(response.status_code, 422)
        data = json.loads(response.data)
        self.assertEqual(data["status"], 422)

    def test_reset_password_with_already_used_token(self):
        """Test that reset token cannot be reused."""
        user = self._create_test_user()

        # Generate and store a token
        token = generate_activation_token(
            SECRET_KEY, PASSWORD_RESET_SALT, self._test_email
        )
        user.last_password_reset_token = token
        db.session.commit()

        # First reset should succeed
        response1 = self.client.post(
            f"/reset-password/{token}",
            data=json.dumps({"password": self._new_password}),
            content_type="application/json",
        )
        self.assertEqual(response1.status_code, 200)

        # Try to use the same token again
        response2 = self.client.post(
            f"/reset-password/{token}",
            data=json.dumps({"password": "AnotherPassword789!"}),
            content_type="application/json",
        )

        # Should return 422 (token already used or invalid)
        self.assertEqual(response2.status_code, 422)

    def test_jwt_session_invalidated_after_password_reset(self):
        """Test that JWT session is invalidated after password reset."""
        user = self._create_test_user()

        # Set a JWT session ID
        user.jwt_session_id = "test_session_id_123"
        db.session.commit()

        # Generate a valid reset token
        token = generate_activation_token(
            SECRET_KEY, PASSWORD_RESET_SALT, self._test_email
        )
        user.last_password_reset_token = token
        db.session.commit()

        response = self.client.post(
            f"/reset-password/{token}",
            data=json.dumps({"password": self._new_password}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)

        # JWT session should be cleared
        updated_user = GwUser.get_by_email(self._test_email)
        self.assertIsNone(updated_user.jwt_session_id)

    def test_forgot_password_rate_limiting(self):
        """Test that forgot-password endpoint is rate limited."""
        # Try 4 requests rapidly (3/hour limit)
        with patch("server.config.mails.mail.send"):
            for i in range(4):
                response = self.client.post(
                    "/forgot-password",
                    data=json.dumps({"email": f"test{i}@example.com"}),
                    content_type="application/json",
                )

                if i < 3:  # First 3 should be OK (3/hour limit)
                    self.assertEqual(response.status_code, 200)
                else:
                    # 4th should hit rate limit
                    self.assertEqual(response.status_code, 429)


if __name__ == "__main__":
    unittest.main()
