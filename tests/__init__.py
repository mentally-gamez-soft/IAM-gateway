"""Declare the base test classfor the tests suit."""

import unittest

from sqlalchemy import text

from core import create_app, db
from core.users.models import (
    GwUser,
    GwUserRole,
    RefreshToken,
    StatsApiEndpoints,
    UserConsent,
)


class BaseTestClass(unittest.TestCase):
    """Define the base test class."""

    def setUp(self):
        """Define the data set create before each test."""
        self.app = create_app(settings_module="config.testing")
        self.client = self.app.test_client()

        # Create the flask context
        with self.app.app_context():
            # Ensure the per-environment schema exists before creating tables.
            # This handles cases where the DB exists but the schema does not
            # (e.g. fresh CI environment, or first run against a new DB).
            _schema = self.app.config.get("SQLALCHEMY_DATABASE_SCHEMA")
            if _schema and _schema.lower() not in ("none", "public", ""):
                db.session.execute(
                    text(f"CREATE SCHEMA IF NOT EXISTS {_schema}")
                )
                db.session.commit()

            db.create_all()

            # Clean up any leftover data from previous runs before inserting
            db.session.query(RefreshToken).delete()
            db.session.query(UserConsent).delete()
            db.session.query(GwUserRole).delete()
            db.session.query(GwUser).delete()
            db.session.query(StatsApiEndpoints).delete()
            db.session.commit()

            # Create a non active user
            BaseTestClass.create_user(
                "guest_non_active", "guest_non_active@xyz.com", "1111", False
            )
            BaseTestClass.create_user(
                "guest_active", "guest_active@xyz.com", "2222", False, True
            )

    def tearDown(self):
        """Destroy the data set after each test."""
        with self.app.app_context():
            # Delete all the data from the DB (order matters: FK constraints)
            db.session.query(RefreshToken).delete()
            db.session.query(UserConsent).delete()
            db.session.query(GwUserRole).delete()
            db.session.query(GwUser).delete()
            db.session.query(StatsApiEndpoints).delete()
            db.session.commit()
            db.session.remove()

    @staticmethod
    def create_user(
        name, email, password, is_admin, is_active=False
    ) -> GwUser:
        """Define an utility method to initiate the dataset.

        Args:
            name (str): the name for a user
            email (str): the email of a user
            password (str): a password for a user
            is_admin (bool): indicate if the user is an admin
            is_active (bool): indicate if the user is active

        Returns:
            User: Returns an instance of a user
        """
        user = GwUser(name, email)
        user.set_password(password)
        user.is_admin = is_admin
        user.active = is_active
        user.save()
        return user

    def login(self, email, password):
        """Declare a utility method to login a user.

        Args:
            email (str): the email of the user
            password (str): the password for a user

        Returns:
            Response: the response
        """
        return self.client.post(
            "/login",
            json=dict(email=email, password=password),
            # follow_redirects=True,
        )

    def logout(self, payload):
        """Declare a utility method to logout a user.

        Returns:
            Response: the response
        """
        return self.client.post(
            "/logout",
            json=payload,
        )

    def add_role(self, payload):
        """Declare a utility method to add a role to a user.

        Returns:
            Response: the response
        """
        return self.client.post(
            "/role/add",
            json=payload,
        )
