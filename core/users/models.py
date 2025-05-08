"""Defines the models for the users module."""

import uuid

import arrow
from flask_login import UserMixin
from sqlalchemy.dialects.postgresql import UUID
from werkzeug.security import check_password_hash, generate_password_hash

from core import db


class GwUser(db.Model, UserMixin):
    """Declare the user model class."""

    __tablename__ = "gw_user"

    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = db.Column(db.String(30), unique=True, nullable=False)
    email = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    last_activation_token = db.Column(
        db.String(500), unique=False, nullable=True
    )
    active = db.Column(db.Boolean, nullable=False, default=False)
    activated_on = db.Column(db.DateTime, nullable=True)
    deactivated_on = db.Column(db.DateTime, nullable=True)
    jwt_session_id = db.Column(db.String(500), nullable=True)
    deleted = db.Column(db.Boolean, nullable=False, default=False)
    role = db.Column(db.String(50), nullable=False, unique=False)
    is_admin = db.Column(db.Boolean, default=False)

    def __init__(self, username, email):
        """Declare constructor for User.

        Args:
            username (str): the username of a user
            email (str): the email of a user
        """
        self.username = username
        self.email = email

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
