"""Defines the models for the users module."""

import uuid

import arrow
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import UUID
from werkzeug.security import check_password_hash, generate_password_hash

from core import db


class GwUserRole(db.Model):
    """Declare the model for the available roles."""

    __tablename__ = "gw_user_role"

    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(50), unique=False, nullable=False)
    gwuser_id = db.Column(
        UUID(as_uuid=True), db.ForeignKey("gw_user.id"), nullable=False
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
        """Save an instance of a user in the database."""
        if not self.id:
            db.session.add(self)
        db.session.commit()


class GwUser(db.Model, UserMixin):
    """Declare the user model class."""

    __tablename__ = "gw_user"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    created_on = db.Column(db.DateTime, nullable=False)
    last_activation_token = db.Column(
        db.String(500), unique=False, nullable=True
    )
    active = db.Column(db.Boolean, nullable=False, default=False)
    activated_on = db.Column(db.DateTime, nullable=True)
    deactivated_on = db.Column(db.DateTime, nullable=True)
    jwt_session_id = db.Column(db.String(500), nullable=True)
    deleted = db.Column(db.Boolean, nullable=False, default=False)
    roles = db.relationship(
        "GwUserRole",
        backref="gwuser",
        lazy=True,
        cascade="all, delete-orphan",
        order_by="asc(GwUserRole.created_on)",
    )
    is_admin = db.Column(db.Boolean, default=False)

    def __init__(self, username, email, role):
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
        self.password = generate_password_hash(password)

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
            db.session.add(self)
        db.session.commit()

    @staticmethod
    def add_role_to_user_by_id(user_id, role):
        """Set the role of a user.

        Args:
            user_id (UUID): ID of the user.
            role (str): The role of the user.
        """
        gw_user_role = GwUserRole(user_id, role)
        if not gw_user_role.id:
            db.session.add(gw_user_role)
        db.session.commit()

    def __repr__(self):
        """Set the representation of an instance of a user.

        Returns:
            str: An instance of a user.
        """
        return f"<User {self.email}>"

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
        db.session.commit()

    def is_active(self):
        """Check if a user is active.

        Returns:
            bool: True if the user is active, False otherwise.
        """
        return self.active

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
        db.session.commit()

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
            return user.roles
        return []

    @staticmethod
    def is_active_user_by_id(id):
        """Check if a user is active.

        Returns:
            bool: True if the user is active, False otherwise.
        """
        return GwUser.get_by_id(id).active

    staticmethod

    def reset_activation_token_by_id(id: UUID, activation_token: str):
        """Set the last activation token for the user.

        Args:
            id (UUID): id of the user.
            activation_token (str): one time activation token.
        """
        GwUser.get_by_id(id).last_activation_token = activation_token
        db.session.commit()
