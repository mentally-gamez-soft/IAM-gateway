"""Defines the models for the users module."""

import hashlib
import uuid
from os import environ as env
from typing import List

import arrow
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped
from werkzeug.security import check_password_hash, generate_password_hash

from core import db, get_session_with_schema


class GwUserRole(db.Model):
    """Declare the model for the available roles."""

    __table_args__ = {
        "schema": "per_env",
        "comment": "Define the role of the user.",
    }
    __tablename__ = "gw_user_role"

    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(50), unique=False, nullable=False)
    gwuser_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("per_env.gw_user.id"), nullable=False
    )
    created_on = db.Column(db.DateTime, nullable=False)

    def __init__(self, user_id, role):
        """Declare constructor for user role.

        Args:
            user_id (uuid): the uuid of a user
            role (str): the role of a user
        """
        self.role = role
        self.gwuser_id = user_id
        self.created_on = arrow.utcnow().datetime

    def save(self):
        """Save an instance of a user role in the database."""
        if not self.id:
            get_session_with_schema().add(self)
        get_session_with_schema().commit()


class GwUser(db.Model, UserMixin):
    """Declare the user model class."""

    __table_args__ = {
        "schema": "per_env",
        "comment": "Define the properties of the user.",
    }
    __tablename__ = "gw_user"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(500), nullable=False)
    created_on = db.Column(db.DateTime, nullable=False)
    last_activation_token = db.Column(
        db.String(100), unique=False, nullable=True
    )
    last_password_reset_token = db.Column(
        db.String(100), unique=False, nullable=True
    )
    active = db.Column(db.Boolean, nullable=False, default=False)
    activated_on = db.Column(db.DateTime, nullable=True)
    deactivated_on = db.Column(db.DateTime, nullable=True)
    jwt_session_id = db.Column(db.String(500), nullable=True)
    deleted = db.Column(db.Boolean, nullable=False, default=False)
    deleted_at = db.Column(db.DateTime, nullable=True)
    consent_given = db.Column(db.Boolean, nullable=True, default=None)
    consent_at = db.Column(db.DateTime, nullable=True)
    roles: Mapped[List["GwUserRole"]] = db.relationship(
        "GwUserRole",
        backref="gwuser",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="asc(GwUserRole.created_on)",
    )
    is_admin = db.Column(db.Boolean, default=False)

    # Profile fields (US-011)
    display_name = db.Column(db.String(80), nullable=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    language_preference = db.Column(db.String(5), nullable=False, default="en")
    timezone = db.Column(db.String(50), nullable=False, default="UTC")
    profile_updated_at = db.Column(db.DateTime, nullable=True)

    def __init__(self, username, email):
        """Declare constructor for User.

        Args:
            username (str): the username of a user
            email (str): the email of a user
        """
        self.username = username
        self.email = email
        self.created_on = arrow.utcnow().datetime

    def set_password(self, password):
        """Set the assword for a user.

        Args:
            password (str): the chosen password.
        """
        self.password = generate_password_hash(
            password=password, salt_length=25
        )

    def check_password(self, password):
        """Control that a given password is correct.

        Args:
            password (str): the password t ocheck.

        Returns:
            bool: True if the given password is the same as the stored one, False otherwise.
        """
        return check_password_hash(self.password, password)

    def save(self):
        """Save an instance of a user in the database."""
        if not self.id:
            get_session_with_schema().add(self)
        get_session_with_schema().commit()

    @staticmethod
    def add_role_to_user_by_id(user_id, role):
        """Set the role of a user.

        Args:
            user_id (UUID): ID of the user.
            role (str): The role of the user.
        """
        gw_user_role = GwUserRole(user_id, role)
        if not gw_user_role.id:
            get_session_with_schema().add(gw_user_role)
        get_session_with_schema().commit()

    def __repr__(self):
        """Set the representation of an instance of a user.

        Returns:
            str: An instance of a user.
        """
        return f"<User {self.email}>"

    def to_profile_dict(self) -> dict:
        """Serialize the user's profile to a JSON-safe dictionary.

        Returns:
            dict: A dictionary with all profile fields for US-011.
        """
        return {
            "id": str(self.id),
            "username": self.username,
            "email": self.email,
            "display_name": self.display_name,
            "avatar_url": self.avatar_url,
            "bio": self.bio,
            "language_preference": self.language_preference or "en",
            "timezone": self.timezone or "UTC",
            "is_admin": self.is_admin,
            "active": self.active,
            "created_on": (
                self.created_on.isoformat() if self.created_on else None
            ),
            "activated_on": (
                self.activated_on.isoformat() if self.activated_on else None
            ),
            "profile_updated_at": (
                self.profile_updated_at.isoformat()
                if self.profile_updated_at
                else None
            ),
            "roles": [r.role for r in self.roles],
        }

    def update_profile(self, data: dict) -> None:
        """Update mutable profile fields on the user (US-011).

        Protected fields (email, username, password, roles) are silently
        ignored even if present in *data*.

        Args:
            data (dict): Key/value pairs of fields to update.
        """
        allowed = {
            "display_name",
            "avatar_url",
            "bio",
            "language_preference",
            "timezone",
        }
        for field, value in data.items():
            if field in allowed:
                setattr(self, field, value)
        self.profile_updated_at = arrow.utcnow().datetime
        self.save()

    @staticmethod
    def get_by_id(id) -> "GwUser":
        """Retrieve a user according to its ID.

        Args:
            id (int): the ID of a user.

        Returns:
            User: An instance of a user.
        """
        return GwUser.query.get(id)

    @staticmethod
    def get_number_of_users_by_email(email: str) -> int:
        """Retrieve the number of users with a given email.

        Args:
            email (str): the email of a user.

        Returns:
            int: The number of users with the given email.
        """
        return GwUser.query.filter_by(email=email).count()

    @staticmethod
    def get_by_email(email) -> "GwUser":
        """Retrieve a user according to its email.

        Args:
            email (str): the email of a user.

        Returns:
            User: An instance of a user.
        """
        return GwUser.query.filter_by(email=email).first()

    def delete(self):
        """Mark a user as deleted."""
        self.deleted = True
        self.deactivated_on = arrow.utcnow().datetime
        self.deleted_at = arrow.utcnow().datetime
        get_session_with_schema().commit()

    def soft_delete_and_anonymize(self):
        """Soft-delete the user and anonymize all PII fields.

        Sets the deleted flag, records deletion timestamp, revokes all sessions,
        and anonymizes username and email to comply with GDPR right to erasure.
        """
        uid = str(self.id)
        self.deleted = True
        self.deleted_at = arrow.utcnow().datetime
        self.deactivated_on = self.deleted_at
        self.active = False
        self.jwt_session_id = None
        self.email = f"deleted_{uid}@deleted.invalid"
        self.username = f"deleted_{uid[:8]}"
        get_session_with_schema().commit()

    def export_data(self) -> dict:
        """Export all user personal data as a structured dictionary.

        Returns:
            dict: All user-owned data for GDPR Article 20 portability.
        """
        return {
            "account": {
                "id": str(self.id),
                "username": self.username,
                "email": self.email,
                "created_on": (
                    self.created_on.isoformat() if self.created_on else None
                ),
                "activated_on": (
                    self.activated_on.isoformat()
                    if self.activated_on
                    else None
                ),
                "is_active": self.active,
                "is_admin": self.is_admin,
                "consent_given": self.consent_given,
                "consent_at": (
                    self.consent_at.isoformat() if self.consent_at else None
                ),
            },
            "roles": [role.role for role in self.roles],
            "consents": [
                {
                    "consent_type": c.consent_type,
                    "granted": c.granted,
                    "granted_at": (
                        c.granted_at.isoformat() if c.granted_at else None
                    ),
                    "revoked_at": (
                        c.revoked_at.isoformat() if c.revoked_at else None
                    ),
                    "ip_address": c.ip_address,
                }
                for c in UserConsent.get_all_for_user(self.id)
            ],
            "export_metadata": {
                "export_date": arrow.utcnow().isoformat(),
                "format_version": "1.0",
            },
        }

    def update_consent(self, consent_given: bool, ip_address: str = None):
        """Update the user-level GDPR consent.

        Args:
            consent_given (bool): Whether the user has given consent.
            ip_address (str, optional): The IP address of the requester.
        """
        self.consent_given = consent_given
        self.consent_at = arrow.utcnow().datetime
        get_session_with_schema().commit()

    def is_active(self) -> bool:
        """Check if a user is active.

        A user is considered active only when their ``active`` flag is True
        **and** their account has not been soft-deleted.

        Returns:
            bool: True if the user is active and not deleted, False otherwise.
        """
        return self.active and not self.deleted

    @staticmethod
    def activate_by_id(id) -> "GwUser":
        """Mark a user as activated..

        Args:
            id (int): the ID of a user.

        Returns:
            User: An instance of a user.
        """
        gw_user = GwUser.query.get(id)
        gw_user.active = True
        gw_user.activated_on = arrow.utcnow().datetime
        get_session_with_schema().commit()

        return gw_user

    @staticmethod
    def get_all():
        """Retrieve the list of all the users."""
        return GwUser.query.all()

    @staticmethod
    def get_user_roles_by_id(id) -> list:
        """Retrieve the list of all roles of the user.

        Args:
            id (UUID): The id of the user.

        Returns:
            list: All the roles of a user.
        """
        user = GwUser.get_by_id(id)
        if user:
            return [role.role for role in user.roles]
        return []

    @staticmethod
    def is_active_user_by_id(id):
        """Check if a user is active.

        Returns:
            bool: True if the user is active, False otherwise.
        """
        return GwUser.get_by_id(id).active

    @staticmethod
    def reset_activation_token_by_id(id: UUID, activation_token: str):
        """Set the last activation token for the user.

        Args:
            id (UUID): id of the user.
            activation_token (str): one time activation token.
        """
        GwUser.get_by_id(id).last_activation_token = activation_token
        get_session_with_schema().commit()


class RefreshToken(db.Model):
    """Model for storing refresh tokens with rotation and revocation support."""

    __table_args__ = {
        "schema": "per_env",
        "comment": "Stores refresh tokens with family-based reuse detection.",
    }
    __tablename__ = "refresh_token"

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(255), unique=True, nullable=False)  # hashed
    user_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("per_env.gw_user.id"), nullable=False
    )
    family_id = db.Column(
        UUID(as_uuid=True), nullable=False, default=uuid.uuid4
    )
    created_on = db.Column(
        db.DateTime, nullable=False, default=arrow.utcnow().datetime
    )
    expires_on = db.Column(db.DateTime, nullable=False)
    revoked = db.Column(db.Boolean, nullable=False, default=False)
    revoked_on = db.Column(db.DateTime, nullable=True)
    replaced_by = db.Column(db.String(255), nullable=True)  # hash of new token

    user = db.relationship(
        "GwUser",
        backref=db.backref(
            "refresh_tokens", cascade="all, delete-orphan", lazy=True
        ),
    )

    def __init__(
        self, user_id: UUID, expires_on: arrow.Arrow, family_id: UUID = None
    ):
        """Initialize a refresh token.

        Args:
            user_id (UUID): The ID of the user
            expires_on (arrow.Arrow): Expiration datetime
            family_id (UUID, optional): Token family for reuse detection
        """
        self.user_id = user_id
        self.expires_on = (
            expires_on.datetime
            if hasattr(expires_on, "datetime")
            else expires_on
        )
        self.family_id = family_id or uuid.uuid4()
        self.created_on = arrow.utcnow().datetime

    @staticmethod
    def hash_token(token: str) -> str:
        """Hash a refresh token for storage.

        Args:
            token (str): Raw refresh token

        Returns:
            str: SHA-256 hash of the token
        """
        return hashlib.sha256(token.encode()).hexdigest()

    def is_expired(self) -> bool:
        """Check if the token has expired.

        Returns:
            bool: True if expired, False otherwise
        """
        return arrow.utcnow() > arrow.get(self.expires_on)

    def is_valid(self) -> bool:
        """Check if the token is valid (not revoked and not expired).

        Returns:
            bool: True if valid, False otherwise
        """
        return not self.revoked and not self.is_expired()

    def revoke(self):
        """Mark this token as revoked."""
        self.revoked = True
        self.revoked_on = arrow.utcnow().datetime
        get_session_with_schema().commit()

    @staticmethod
    def get_by_token(token_hash: str) -> "RefreshToken":
        """Retrieve a refresh token by its hash.

        Args:
            token_hash (str): SHA-256 hash of the refresh token

        Returns:
            RefreshToken: The token if found, None otherwise
        """
        return RefreshToken.query.filter_by(token=token_hash).first()

    @staticmethod
    def revoke_all_for_user(user_id: UUID):
        """Revoke all refresh tokens for a user.

        Args:
            user_id (UUID): The user ID
        """
        tokens = RefreshToken.query.filter_by(
            user_id=user_id, revoked=False
        ).all()
        for token in tokens:
            token.revoke()

    @staticmethod
    def revoke_family(family_id: UUID):
        """Revoke all tokens in a family (reuse detection).

        Args:
            family_id (UUID): The family ID
        """
        tokens = RefreshToken.query.filter_by(
            family_id=family_id, revoked=False
        ).all()
        for token in tokens:
            token.revoke()

    def save(self):
        """Save this refresh token to the database."""
        if not self.id:
            get_session_with_schema().add(self)
        get_session_with_schema().commit()

    def __repr__(self):
        """Return string representation."""
        return f"<RefreshToken user_id={self.user_id} expired={self.is_expired()}>"


class StatsApiEndpoints(db.Model):
    """Declare the model for the statistic on endpoints calls."""

    __table_args__ = {
        "schema": "per_env",
        "comment": "Define the statistic for the calls of endpoints.",
    }
    __tablename__ = "stats_api_endpoints"

    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, nullable=False, default=1)
    endpoint_url = db.Column(db.String(500), unique=True, nullable=False)

    @staticmethod
    def get_api_endpoint(api_endpoint) -> "StatsApiEndpoints":
        """Retrieve an endpoint.

        Args:
            api_endpoint (str): the api endpoint.

        Returns:
            StatsApiEndpoints: An instance of stat endpoint.
        """
        return StatsApiEndpoints.query.filter_by(
            endpoint_url=api_endpoint
        ).first()

    @staticmethod
    def increment_counter_api_endpoint(api_endpoint) -> "StatsApiEndpoints":
        """Increment the call number counter of an endpoint.

        Args:
            api_endpoint (str): the api endpoint.

        Returns:
            StatsApiEndpoints: An instance of stat endpoint.
        """
        stats_end_point = StatsApiEndpoints.get_api_endpoint(api_endpoint)
        if stats_end_point:
            stats_end_point.count = stats_end_point.count + 1
        else:
            stats_end_point = StatsApiEndpoints(endpoint_url=api_endpoint)
        stats_end_point.save()

    def save(self):
        """Save an instance of a stats endpoints in the database."""
        if not self.id:
            get_session_with_schema().add(self)
        get_session_with_schema().commit()


class UserConsent(db.Model):
    """Declare the model for per-type GDPR consent records."""

    __table_args__ = {
        "schema": "per_env",
        "comment": "Tracks GDPR consent entries per user per consent type.",
    }
    __tablename__ = "user_consent"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("per_env.gw_user.id"), nullable=False
    )
    consent_type = db.Column(db.String(50), nullable=False)
    granted = db.Column(db.Boolean, nullable=False, default=False)
    granted_at = db.Column(db.DateTime, nullable=True)
    revoked_at = db.Column(db.DateTime, nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)

    user = db.relationship(
        "GwUser",
        backref=db.backref(
            "consents", cascade="all, delete-orphan", lazy=True
        ),
    )

    def __init__(
        self,
        user_id: UUID,
        consent_type: str,
        granted: bool,
        ip_address: str = None,
    ):
        """Initialize a consent record.

        Args:
            user_id (UUID): The ID of the user.
            consent_type (str): The type of consent (e.g. 'marketing', 'analytics').
            granted (bool): Whether the consent was granted.
            ip_address (str, optional): Requester IP address for audit trail.
        """
        self.user_id = user_id
        self.consent_type = consent_type
        self.granted = granted
        self.ip_address = ip_address
        self.granted_at = arrow.utcnow().datetime if granted else None

    def revoke(self):
        """Mark this consent as revoked."""
        self.granted = False
        self.revoked_at = arrow.utcnow().datetime
        get_session_with_schema().commit()

    def save(self):
        """Save this consent record to the database."""
        if not self.id:
            get_session_with_schema().add(self)
        get_session_with_schema().commit()

    @staticmethod
    def get_all_for_user(user_id: UUID) -> list:
        """Return all consent records for a given user.

        Args:
            user_id (UUID): The user's ID.

        Returns:
            list: All UserConsent instances for this user.
        """
        return UserConsent.query.filter_by(user_id=user_id).all()

    @staticmethod
    def upsert(
        user_id: UUID, consent_type: str, granted: bool, ip_address: str = None
    ) -> "UserConsent":
        """Create or update a consent record for a given (user, consent_type) pair.

        Args:
            user_id (UUID): The user's ID.
            consent_type (str): The type of consent.
            granted (bool): Whether consent is granted.
            ip_address (str, optional): Requester IP address.

        Returns:
            UserConsent: The created or updated consent record.
        """
        existing = UserConsent.query.filter_by(
            user_id=user_id, consent_type=consent_type
        ).first()
        if existing:
            if granted:
                existing.granted = True
                existing.granted_at = arrow.utcnow().datetime
                existing.revoked_at = None
            else:
                existing.revoke()
            existing.ip_address = ip_address
            get_session_with_schema().commit()
            return existing
        record = UserConsent(
            user_id=user_id,
            consent_type=consent_type,
            granted=granted,
            ip_address=ip_address,
        )
        record.save()
        return record

    def __repr__(self):
        """Return string representation."""
        return f"<UserConsent user_id={self.user_id} type={self.consent_type} granted={self.granted}>"
