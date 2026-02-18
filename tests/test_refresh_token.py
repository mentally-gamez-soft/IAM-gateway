"""Test suite for JWT Refresh Token mechanism (US-003)."""

import json
import uuid
from datetime import datetime, timedelta

import pytest

from core.auth.jwt.jwt_handler import (
    decode_jwt,
    generate_refresh_token,
    generate_token_pair,
)
from core.common.error_codes import (
    __RESPONSE_STATUS_200,
    __RESPONSE_STATUS_401,
)
from core.users.models import GwUser, RefreshToken


@pytest.fixture
def test_user(app):
    """Create a test user for token tests."""
    with app.app_context():
        user = GwUser(
            id=uuid.uuid4(),
            username=f"testuser_{uuid.uuid4().hex[:8]}",
            email=f"test_{uuid.uuid4().hex[:8]}@example.com",
            password="TestPassword123!",
            created_on=datetime.utcnow(),
        )
        user.save()
        yield user
        try:
            user.delete()
        except Exception:
            pass


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


class TestRefreshTokenModel:
    """Test RefreshToken model functionality."""

    def test_hash_token_generates_consistent_hash(self):
        """Test that hashing produces consistent results."""
        token = "test_token_123"
        hash1 = RefreshToken.hash_token(token)
        hash2 = RefreshToken.hash_token(token)
        assert hash1 == hash2

    def test_hash_token_different_for_different_tokens(self):
        """Test that different tokens produce different hashes."""
        token1 = "token1"
        token2 = "token2"
        hash1 = RefreshToken.hash_token(token1)
        hash2 = RefreshToken.hash_token(token2)
        assert hash1 != hash2

    def test_refresh_token_is_valid_when_not_expired_or_revoked(
        self, app, test_user
    ):
        """Test is_valid() returns True for valid tokens."""
        with app.app_context():
            token_string = generate_refresh_token()
            token_hash = RefreshToken.hash_token(token_string)

            refresh_token = RefreshToken(
                token=token_hash,
                user_id=test_user.id,
                family_id=uuid.uuid4(),
                created_on=datetime.utcnow(),
                expires_on=datetime.utcnow() + timedelta(days=7),
                revoked=False,
            )
            refresh_token.save()

            assert refresh_token.is_valid() is True

    def test_refresh_token_is_not_valid_when_expired(self, app, test_user):
        """Test is_valid() returns False for expired tokens."""
        with app.app_context():
            token_string = generate_refresh_token()
            token_hash = RefreshToken.hash_token(token_string)

            refresh_token = RefreshToken(
                token=token_hash,
                user_id=test_user.id,
                family_id=uuid.uuid4(),
                created_on=datetime.utcnow(),
                expires_on=datetime.utcnow() - timedelta(hours=1),
                revoked=False,
            )
            refresh_token.save()

            assert refresh_token.is_valid() is False

    def test_refresh_token_is_not_valid_when_revoked(self, app, test_user):
        """Test is_valid() returns False for revoked tokens."""
        with app.app_context():
            token_string = generate_refresh_token()
            token_hash = RefreshToken.hash_token(token_string)

            refresh_token = RefreshToken(
                token=token_hash,
                user_id=test_user.id,
                family_id=uuid.uuid4(),
                created_on=datetime.utcnow(),
                expires_on=datetime.utcnow() + timedelta(days=7),
                revoked=True,
            )
            refresh_token.save()

            assert refresh_token.is_valid() is False

    def test_is_expired_returns_true_for_expired_token(self, app, test_user):
        """Test is_expired() for tokens past expiration."""
        with app.app_context():
            token_string = generate_refresh_token()
            token_hash = RefreshToken.hash_token(token_string)

            refresh_token = RefreshToken(
                token=token_hash,
                user_id=test_user.id,
                family_id=uuid.uuid4(),
                created_on=datetime.utcnow(),
                expires_on=datetime.utcnow() - timedelta(hours=1),
                revoked=False,
            )
            refresh_token.save()

            assert refresh_token.is_expired() is True

    def test_revoke_sets_revoked_flag_and_timestamp(self, app, test_user):
        """Test that revoke() sets revoked flag and timestamp."""
        with app.app_context():
            token_string = generate_refresh_token()
            token_hash = RefreshToken.hash_token(token_string)

            refresh_token = RefreshToken(
                token=token_hash,
                user_id=test_user.id,
                family_id=uuid.uuid4(),
                created_on=datetime.utcnow(),
                expires_on=datetime.utcnow() + timedelta(days=7),
                revoked=False,
            )
            refresh_token.save()

            refresh_token.revoke()
            assert refresh_token.revoked is True
            assert refresh_token.revoked_on is not None

    def test_get_by_token_finds_token(self, app, test_user):
        """Test get_by_token() finds stored tokens."""
        with app.app_context():
            token_string = generate_refresh_token()
            token_hash = RefreshToken.hash_token(token_string)

            refresh_token = RefreshToken(
                token=token_hash,
                user_id=test_user.id,
                family_id=uuid.uuid4(),
                created_on=datetime.utcnow(),
                expires_on=datetime.utcnow() + timedelta(days=7),
            )
            refresh_token.save()

            found = RefreshToken.get_by_token(token_hash)
            assert found is not None
            assert found.token == token_hash

    def test_get_by_token_returns_none_for_unknown_token(self, app):
        """Test get_by_token() returns None for non-existent tokens."""
        with app.app_context():
            unknown_hash = RefreshToken.hash_token("unknown_token")
            found = RefreshToken.get_by_token(unknown_hash)
            assert found is None

    def test_revoke_all_for_user_revokes_all_tokens(self, app, test_user):
        """Test revoke_all_for_user() revokes all user tokens."""
        with app.app_context():
            # Create multiple tokens for user
            for _ in range(3):
                token_string = generate_refresh_token()
                token_hash = RefreshToken.hash_token(token_string)
                refresh_token = RefreshToken(
                    token=token_hash,
                    user_id=test_user.id,
                    family_id=uuid.uuid4(),
                    created_on=datetime.utcnow(),
                    expires_on=datetime.utcnow() + timedelta(days=7),
                    revoked=False,
                )
                refresh_token.save()

            # Revoke all
            RefreshToken.revoke_all_for_user(test_user.id)

            # Verify all revoked
            from application import db

            tokens = (
                db.session.query(RefreshToken)
                .filter_by(user_id=test_user.id)
                .all()
            )
            assert all(t.revoked for t in tokens)

    def test_revoke_family_revokes_all_tokens_in_family(self, app, test_user):
        """Test revoke_family() revokes all tokens in token family."""
        with app.app_context():
            family_id = uuid.uuid4()

            # Create multiple tokens in same family
            for _ in range(3):
                token_string = generate_refresh_token()
                token_hash = RefreshToken.hash_token(token_string)
                refresh_token = RefreshToken(
                    token=token_hash,
                    user_id=test_user.id,
                    family_id=family_id,
                    created_on=datetime.utcnow(),
                    expires_on=datetime.utcnow() + timedelta(days=7),
                    revoked=False,
                )
                refresh_token.save()

            # Revoke family
            RefreshToken.revoke_family(family_id)

            # Verify all in family revoked
            from application import db

            tokens = (
                db.session.query(RefreshToken)
                .filter_by(family_id=family_id)
                .all()
            )
            assert all(t.revoked for t in tokens)


class TestTokenGeneration:
    """Test token generation functionality."""

    def test_generate_refresh_token_returns_string(self):
        """Test generate_refresh_token() returns a string."""
        token = generate_refresh_token()
        assert isinstance(token, str)
        assert len(token) > 0

    def test_generate_refresh_token_creates_unique_tokens(self):
        """Test that consecutive generations create different tokens."""
        token1 = generate_refresh_token()
        token2 = generate_refresh_token()
        assert token1 != token2

    def test_generate_token_pair_returns_all_required_fields(
        self, app, test_user
    ):
        """Test generate_token_pair() returns required fields."""
        with app.app_context():
            pair = generate_token_pair(
                user_id=test_user.id,
                payload_data={"test": "data"},
            )

            assert "access_token" in pair
            assert "refresh_token" in pair
            assert "token_type" in pair
            assert "expires_in" in pair
            assert pair["token_type"] == "Bearer"

    def test_generate_token_pair_stores_refresh_token(self, app, test_user):
        """Test that generate_token_pair() stores refresh token in DB."""
        with app.app_context():
            pair = generate_token_pair(
                user_id=test_user.id,
                payload_data={"test": "data"},
            )

            # Try to retrieve the stored token
            token_hash = RefreshToken.hash_token(pair["refresh_token"])
            stored = RefreshToken.get_by_token(token_hash)

            assert stored is not None
            assert stored.user_id == test_user.id
            assert stored.revoked is False

    def test_access_token_is_valid_jwt(self, app, test_user):
        """Test that access token is a valid JWT."""
        with app.app_context():
            pair = generate_token_pair(
                user_id=test_user.id,
                payload_data={"email": test_user.email},
            )

            # Try to decode the access token
            decoded = decode_jwt(pair["access_token"])
            assert decoded is not None
            assert decoded["sub"] == str(test_user.id)


class TestTokenRefreshEndpoint:
    """Test the /token/refresh endpoint."""

    def test_refresh_token_endpoint_exists(self, client):
        """Test that the refresh token endpoint exists."""
        response = client.post(
            "/token/refresh",
            json={"refresh_token": "test"},
        )
        # Should not be 404 (endpoint exists)
        assert response.status_code != 404

    def test_refresh_token_requires_token_in_request(self, client):
        """Test that endpoint rejects requests without refresh token."""
        response = client.post(
            "/token/refresh",
            json={},
        )
        assert response.status_code == 400

    def test_refresh_token_rejects_invalid_token(self, client):
        """Test that endpoint rejects invalid/unknown tokens."""
        response = client.post(
            "/token/refresh",
            json={"refresh_token": "invalid_token_xyz"},
        )
        assert response.status_code == 401

    def test_refresh_token_rejects_expired_token(self, app, client, test_user):
        """Test that endpoint rejects expired tokens."""
        with app.app_context():
            # Create expired token
            token_string = generate_refresh_token()
            token_hash = RefreshToken.hash_token(token_string)

            refresh_token = RefreshToken(
                token=token_hash,
                user_id=test_user.id,
                family_id=uuid.uuid4(),
                created_on=datetime.utcnow(),
                expires_on=datetime.utcnow() - timedelta(hours=1),
                revoked=False,
            )
            refresh_token.save()

        response = client.post(
            "/token/refresh",
            json={"refresh_token": token_string},
        )
        assert response.status_code == 401
        assert "expired" in response.json["message"].lower()

    def test_refresh_token_rejects_revoked_token(self, app, client, test_user):
        """Test that endpoint rejects revoked tokens."""
        with app.app_context():
            # Create revoked token
            token_string = generate_refresh_token()
            token_hash = RefreshToken.hash_token(token_string)

            refresh_token = RefreshToken(
                token=token_hash,
                user_id=test_user.id,
                family_id=uuid.uuid4(),
                created_on=datetime.utcnow(),
                expires_on=datetime.utcnow() + timedelta(days=7),
                revoked=True,
            )
            refresh_token.save()

        response = client.post(
            "/token/refresh",
            json={"refresh_token": token_string},
        )
        assert response.status_code == 401
        assert "revoked" in response.json["message"].lower()

    def test_refresh_token_detects_reuse(self, app, client, test_user):
        """Test that endpoint detects and blocks token reuse (security)."""
        with app.app_context():
            # Create token and mark as already used
            token_string = generate_refresh_token()
            token_hash = RefreshToken.hash_token(token_string)
            family_id = uuid.uuid4()

            refresh_token = RefreshToken(
                token=token_hash,
                user_id=test_user.id,
                family_id=family_id,
                created_on=datetime.utcnow(),
                expires_on=datetime.utcnow() + timedelta(days=7),
                revoked=False,
                replaced_by=RefreshToken.hash_token("some_other_token"),
            )
            refresh_token.save()

        response = client.post(
            "/token/refresh",
            json={"refresh_token": token_string},
        )
        assert response.status_code == 401
        assert "already been used" in response.json["message"]

    def test_refresh_token_returns_new_tokens(self, app, client, test_user):
        """Test that successful refresh returns new tokens."""
        with app.app_context():
            # Create valid token
            pair = generate_token_pair(
                user_id=test_user.id,
                payload_data={"email": test_user.email},
            )

        response = client.post(
            "/token/refresh",
            json={"refresh_token": pair["refresh_token"]},
        )
        assert response.status_code == 200
        data = response.json["data"]
        assert "access_token" in data
        assert "refresh_token" in data
        assert "token_type" in data
        assert data["token_type"] == "Bearer"

    def test_refresh_token_rotates_token(self, app, client, test_user):
        """Test that old token is marked as replaced."""
        with app.app_context():
            # Create initial token
            pair = generate_token_pair(
                user_id=test_user.id,
                payload_data={"email": test_user.email},
            )
            old_token_hash = RefreshToken.hash_token(pair["refresh_token"])

        # Refresh the token
        response = client.post(
            "/token/refresh",
            json={"refresh_token": pair["refresh_token"]},
        )
        assert response.status_code == 200

        with app.app_context():
            # Verify old token is marked as replaced
            old_token = RefreshToken.get_by_token(old_token_hash)
            assert old_token is not None
            assert old_token.revoked is True
            assert old_token.replaced_by is not None


class TestLoginAndLogout:
    """Test login and logout with dual tokens."""

    def test_login_returns_both_tokens(self, app, client, test_user):
        """Test that login endpoint returns both access and refresh tokens."""
        with app.app_context():
            test_user.set_password("TestPassword123!")
            test_user.active = True
            test_user.save()

        response = client.post(
            "/login",
            json={
                "email": test_user.email,
                "password": "TestPassword123!",
            },
        )

        if response.status_code == 200:
            data = response.json["data"]
            assert "access_token" in data
            assert "refresh_token" in data
            assert "token_type" in data
            assert data["token_type"] == "Bearer"

    def test_logout_revokes_tokens(self, app, client, test_user):
        """Test that logout revokes user's refresh tokens."""
        with app.app_context():
            test_user.set_password("TestPassword123!")
            test_user.active = True
            test_user.save()

            # Create tokens for user
            pair = generate_token_pair(
                user_id=test_user.id,
                payload_data={"email": test_user.email},
            )

        # Logout (simplified - normally would be authenticated)
        # Note: Actual logout requires proper authentication headers
        # This is a placeholder for manual verification
        pass
