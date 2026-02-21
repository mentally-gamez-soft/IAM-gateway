import json
import unittest

from config.default import SECRET_KEY, SECURITY_PASSWORD_SALT
from core.auth.middlewares.validation_token import generate_activation_token
from core.users.models import GwUser, StatsApiEndpoints

from . import BaseTestClass


class BlogClientTestCase(BaseTestClass):
    __SKIP_ALL__: bool = False
    __PROTECTED_ENDPOINTS__: bool = True
    __ROLE_ENDPOINTS__: bool = True
    __LOGIN_LOGOUT_ENDPOINTS__: bool = True
    __STATISTICS_ENDPOINTS__: bool = True
    __EMAIL_ACTIVATION_TOKEN_ENDPOINTS__: bool = True
    __SIGNUP_ENDPOINTS__: bool = True

    @unittest.skipIf(
        __SKIP_ALL__, "Deactivate to execute latest created test."
    )
    @unittest.skipUnless(
        __PROTECTED_ENDPOINTS__, "Family of tests for the protected end points"
    )
    def test_unauthorized_access(self):
        tampered_payload = {"data": {"user": "1234566", "jwt": "Fake.Jwt"}}
        res = self.client.get("/protected", json=tampered_payload)
        data = json.loads(res.data)

        self.assertEqual(401, res.status_code)
        self.assertIn("Access denied!", data["message"])

    @unittest.skipIf(
        __SKIP_ALL__, "Deactivate to execute latest created test."
    )
    @unittest.skipUnless(
        __LOGIN_LOGOUT_ENDPOINTS__,
        "Family of tests for the login/logout endpoints.",
    )
    def test_login_when_user_is_not_active(self):
        email = "guest_non_active@xyz.com"
        password = "1111"
        res = self.login(email, password)
        data = json.loads(res.data)

        self.assertEqual(403, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertNotIn("jwt", data)
        self.assertNotIn("user", data)
        self.assertIn("Account activation required", data.get("message"))

    @unittest.skipIf(
        __SKIP_ALL__, "Deactivate to execute latest created test."
    )
    @unittest.skipUnless(
        __LOGIN_LOGOUT_ENDPOINTS__,
        "Family of tests for the login/logout endpoints.",
    )
    def test_login_when_user_is_active(self):
        email = "guest_active@xyz.com"
        password = "2222"
        res = self.login(email, password)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertIsNotNone(res.headers.get("X-CSRFToken"))
        self.assertIsNotNone(data["data"]["user"])
        self.assertIsNotNone(data["data"]["access_token"])
        self.assertIn("You are now logged in.", data.get("message"))

    @unittest.skipIf(
        __SKIP_ALL__, "Deactivate to execute latest created test."
    )
    @unittest.skipUnless(
        __PROTECTED_ENDPOINTS__, "Family of tests for the protected end points"
    )
    def test_protected_route_when_user_logged_in(self):
        email = "guest_active@xyz.com"
        password = "2222"
        # Connection to the app
        res = self.login(email, password)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertIsNotNone(res.headers.get("X-CSRFToken"))
        self.assertIsNotNone(data["data"]["user"])
        self.assertIsNotNone(data["data"]["access_token"])
        self.assertIn("You are now logged in.", data.get("message"))

        # Request endpoint that requires authentication
        payload = data
        res = self.client.get("/protected", json=payload)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertIsNotNone(res.headers.get("X-CSRFToken"))
        self.assertIsNotNone(data["data"]["user"])
        self.assertIsNotNone(data["data"]["jwt"])
        self.assertIn("Welcome to Gateway-IAM-Proxy service.", data["message"])

    @unittest.skipIf(
        __SKIP_ALL__, "Deactivate to execute latest created test."
    )
    @unittest.skipUnless(
        __LOGIN_LOGOUT_ENDPOINTS__,
        "Family of tests for the login/logout endpoints.",
    )
    def test_user_logging_out(self):
        email = "guest_active@xyz.com"
        password = "2222"
        # Connect to the app
        res = self.login(email, password)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertIsNotNone(res.headers.get("X-CSRFToken"))
        self.assertIsNotNone(data["data"]["user"])
        self.assertIsNotNone(data["data"]["access_token"])
        self.assertIn("You are now logged in.", data.get("message"))

        # Disconnect from the app.
        res = self.logout(data)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertIsNotNone(res.headers.get("X-CSRFToken"))
        self.assertIsNone(data.get("data"))
        self.assertIn("You are now logged out.", data.get("message"))

    @unittest.skipIf(
        __SKIP_ALL__, "Deactivate to execute latest created test."
    )
    @unittest.skipUnless(
        __PROTECTED_ENDPOINTS__, "Family of tests for the protected end points"
    )
    def test_protected_route_after_user_logged_out(self):
        email = "guest_active@xyz.com"
        password = "2222"
        # Connect to the app
        res = self.login(email, password)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertIsNotNone(res.headers.get("X-CSRFToken"))
        self.assertIsNotNone(data["data"]["user"])
        self.assertIsNotNone(data["data"]["access_token"])
        self.assertIn("You are now logged in.", data.get("message"))

        # Disconnect from the app.
        res = self.logout(data)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertIsNotNone(res.headers.get("X-CSRFToken"))
        self.assertIsNone(data.get("data"))
        self.assertIn("You are now logged out.", data.get("message"))

        # request protected endpoint
        res = self.client.get("/protected", json={})
        data = json.loads(res.data)

        self.assertEqual(401, res.status_code)
        self.assertIn("Access denied!", data["message"])

    @unittest.skipIf(
        __SKIP_ALL__, "Deactivate to execute latest created test."
    )
    @unittest.skipUnless(
        __ROLE_ENDPOINTS__,
        "Family of tests for role CRUD operations endpoints.",
    )
    def test_add_role_to_user_when_logged_in(self):
        email = "guest_active@xyz.com"
        password = "2222"
        role = "Artist"

        # Connect to the app
        res = self.login(email, password)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertIsNotNone(res.headers.get("X-CSRFToken"))
        self.assertIsNotNone(data["data"]["user"])
        self.assertIsNotNone(data["data"]["access_token"])
        self.assertIn("You are now logged in.", data.get("message"))

        # Add the role "artist"
        data["data"]["role"] = role
        res = self.add_role(data)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertIsNotNone(res.headers.get("X-CSRFToken"))
        self.assertIsNotNone(data["data"]["user"])
        self.assertIsNotNone(data["data"]["jwt"])
        self.assertIn(
            "The new role has been added successfully to user.",
            data.get("message"),
        )

        # Check the user has the new role
        with self.app.app_context():
            user = GwUser.get_by_email(email)

            self.assertGreaterEqual(1, len(user.roles))
            self.assertEqual(user.roles[0].role, role)

    @unittest.skipIf(
        __SKIP_ALL__, "Deactivate to execute latest created test."
    )
    @unittest.skipUnless(
        __ROLE_ENDPOINTS__,
        "Family of tests for role CRUD operations endpoints.",
    )
    def test_add_role_to_user_when_logged_in_without_role_in_payload(self):
        email = "guest_active@xyz.com"
        password = "2222"
        role = "Artist"

        # Connect to the app
        res = self.login(email, password)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertIsNotNone(res.headers.get("X-CSRFToken"))
        self.assertIsNotNone(data["data"]["user"])
        self.assertIsNotNone(data["data"]["access_token"])
        self.assertIn("You are now logged in.", data.get("message"))

        # Add the role "artist"
        data["data"]["no-role"] = role
        res = self.add_role(data)
        data = json.loads(res.data)

        self.assertEqual(422, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertIsNotNone(res.headers.get("X-CSRFToken"))
        self.assertIn(
            "The provided data input is invalid!", data.get("message")
        )

        # Check the role has not been added to user
        with self.app.app_context():
            user = GwUser.get_by_email(email)

            self.assertEqual(0, len(user.roles))
            self.assertEqual([], user.roles)

    @unittest.skipIf(
        __SKIP_ALL__, "Deactivate to execute latest created test."
    )
    @unittest.skipUnless(
        __ROLE_ENDPOINTS__,
        "Family of tests for role CRUD operations endpoints.",
    )
    def test_add_role_to_user_when_logged_in_without_user_in_payload(self):
        email = "guest_active@xyz.com"
        password = "2222"
        role = "Artist"

        # Connect to the app
        res = self.login(email, password)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertIsNotNone(res.headers.get("X-CSRFToken"))
        self.assertIsNotNone(data["data"]["user"])
        self.assertIsNotNone(data["data"]["access_token"])
        self.assertIn("You are now logged in.", data.get("message"))

        # Add the role "artist"
        data["data"].pop("user", None)
        data["data"]["role"] = role
        res = self.add_role(data)
        data = json.loads(res.data)

        self.assertEqual(401, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertIsNotNone(res.headers.get("X-CSRFToken"))
        self.assertIn("Access denied!", data.get("message"))

        # Check the role has not been added to user
        with self.app.app_context():
            user = GwUser.get_by_email(email)

            self.assertEqual(0, len(user.roles))
            self.assertEqual([], user.roles)

    @unittest.skipIf(
        __SKIP_ALL__, "Deactivate to execute latest created test."
    )
    @unittest.skipUnless(
        __ROLE_ENDPOINTS__,
        "Family of tests for role CRUD operations endpoints.",
    )
    def test_add_role_to_user_when_logged_in_without_jwt_in_payload(self):
        email = "guest_active@xyz.com"
        password = "2222"
        role = "Artist"

        # Connect to the app
        res = self.login(email, password)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertIsNotNone(res.headers.get("X-CSRFToken"))
        self.assertIsNotNone(data["data"]["user"])
        self.assertIsNotNone(data["data"]["access_token"])
        self.assertIn("You are now logged in.", data.get("message"))

        # Add the role "artist"
        data["data"].pop("access_token", None)
        data["data"]["role"] = role
        res = self.add_role(data)
        data = json.loads(res.data)

        self.assertEqual(401, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertIsNotNone(res.headers.get("X-CSRFToken"))
        self.assertIn("Access denied!", data.get("message"))

        # Check the role has not been added to user
        with self.app.app_context():
            user = GwUser.get_by_email(email)

            self.assertEqual(0, len(user.roles))
            self.assertEqual([], user.roles)

    @unittest.skipIf(
        __SKIP_ALL__, "Deactivate to execute latest created test."
    )
    @unittest.skipUnless(
        __ROLE_ENDPOINTS__,
        "Family of tests for role CRUD operations endpoints.",
    )
    def test_add_role_to_user_when_anonymous(self):
        data = {"data": {"role": "Artist"}}
        res = self.add_role(data)
        data = json.loads(res.data)

        self.assertEqual(401, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertIsNone(data.get("data"))
        self.assertIn("Access denied!", data.get("message"))

    @unittest.skipIf(
        __SKIP_ALL__, "Deactivate to execute latest created test."
    )
    @unittest.skipUnless(
        __STATISTICS_ENDPOINTS__,
        "Family of tests for the endpoints consultation statistics",
    )
    def test_endpoint_calls_counter(self):
        # Creation of various users
        with self.app.app_context():
            BaseTestClass.create_user(
                "Yann", "yann.kubitz@gmail.com", "123456", False, True
            )
            BaseTestClass.create_user(
                "Lauren", "lauren.bacal@xyz.com", "654321", False, True
            )

        # user 1 is logging in => 1 call for login
        res_1 = self.login("yann.kubitz@gmail.com", "123456")
        data_1 = json.loads(res_1.data)

        # user 1 add roles => 3 calls for role
        role = "Artist"
        data_1["data"]["role"] = role
        res_6 = self.add_role(data_1)
        role = "Videast"
        res_7 = self.add_role(data_1)
        role = "StuntMan"
        res_7 = self.add_role(data_1)

        # user 1 test the protected end point  => 3 calls for protected
        res_8 = self.client.get("/protected", json=data_1)
        res_9 = self.client.get("/protected", json=data_1)
        res_10 = self.client.get("/protected", json=data_1)

        # user1 logout => 1 call for logout
        res_11 = self.logout(data_1)

        # user 2 is logging in => 2 calls for login
        res_2 = self.login("lauren.bacal@xyz.com", "654321")
        data_2 = json.loads(res_2.data)

        # user 2 test the protected end point  => 4 calls for protected
        res_8 = self.client.get("/protected", json=data_2)

        # user 2 logout => 2 calls for logout
        res_11 = self.logout(data_1)

        with self.app.app_context():
            self.assertEqual(
                2, StatsApiEndpoints.get_api_endpoint("login").count
            )
            self.assertEqual(
                3, StatsApiEndpoints.get_api_endpoint("role").count
            )
            self.assertEqual(
                4, StatsApiEndpoints.get_api_endpoint("protected").count
            )
            self.assertEqual(
                2, StatsApiEndpoints.get_api_endpoint("logout").count
            )

    @unittest.skipIf(
        __SKIP_ALL__, "Deactivate to execute latest created test."
    )
    @unittest.skipUnless(
        __PROTECTED_ENDPOINTS__, "Family of tests for the protected end points"
    )
    def test_protected_endpoints_with_existing_role(self):
        # Log user in
        email = "guest_active@xyz.com"
        password = "2222"
        res = self.login(email, password)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertIsNotNone(res.headers.get("X-CSRFToken"))
        self.assertIsNotNone(data["data"]["user"])
        self.assertIsNotNone(data["data"]["access_token"])
        self.assertIn("You are now logged in.", data.get("message"))

        # Add role Artist to the user
        role = "Artist"
        data["data"]["role"] = role
        res = self.add_role(data)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertIsNotNone(res.headers.get("X-CSRFToken"))
        self.assertIsNotNone(data["data"]["user"])
        self.assertIsNotNone(data["data"]["jwt"])
        self.assertIn(
            "The new role has been added successfully to user.",
            data.get("message"),
        )

        # Access to endpoint
        res = self.client.get("/protected-role", json=data)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIn("Welcome to Gateway-IAM-Proxy service.", data["message"])

        # User log out
        # Disconnect from the app.
        res = self.logout(data)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertIsNotNone(res.headers.get("X-CSRFToken"))
        self.assertIsNone(data.get("data"))
        self.assertIn("You are now logged out.", data.get("message"))

    @unittest.skipIf(
        __SKIP_ALL__, "Deactivate to execute latest created test."
    )
    @unittest.skipUnless(
        __PROTECTED_ENDPOINTS__, "Family of tests for the protected end points"
    )
    def test_protected_endpoints_with_non_existing_role(self):
        # Log user in
        email = "guest_active@xyz.com"
        password = "2222"
        res = self.login(email, password)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertIsNotNone(res.headers.get("X-CSRFToken"))
        self.assertIsNotNone(data["data"]["user"])
        self.assertIsNotNone(data["data"]["access_token"])
        self.assertIn("You are now logged in.", data.get("message"))

        # Add role Artist to the user
        role = "Artist2"
        data["data"]["role"] = role
        res = self.add_role(data)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertIsNotNone(res.headers.get("X-CSRFToken"))
        self.assertIsNotNone(data["data"]["user"])
        self.assertIsNotNone(data["data"]["jwt"])
        self.assertIn(
            "The new role has been added successfully to user.",
            data.get("message"),
        )

        # Access to endpoint
        res = self.client.get("/protected-role", json=data)
        data = json.loads(res.data)

        self.assertEqual(403, res.status_code)
        self.assertIn("Authorization required.", data["message"])

        # User log out
        # Disconnect from the app.
        res = self.logout(data)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertIsNotNone(res.headers.get("X-CSRFToken"))
        self.assertIsNone(data.get("data"))
        self.assertIn("You are now logged out.", data.get("message"))

    @unittest.skipIf(
        __SKIP_ALL__, "Deactivate to execute latest created test."
    )
    @unittest.skipUnless(
        __EMAIL_ACTIVATION_TOKEN_ENDPOINTS__,
        "Family of tests for the user activation token via email.",
    )
    def test_confirm_user_activation_valid(self):
        email = "guest_non_active@xyz.com"

        activation_token = generate_activation_token(
            SECRET_KEY, SECURITY_PASSWORD_SALT, email
        )

        # Update token for user
        with self.app.app_context():
            user = GwUser.get_by_email(email)
            user.last_activation_token = activation_token
            user.save()

        # Access to endpoint
        res = self.client.get("/confirm/{}".format(activation_token))
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertIn(
            "Congratulations, your account is now activated.",
            data.get("message"),
        )

        # Validate that user is now activated
        with self.app.app_context():
            user = GwUser.get_by_email(email)
            self.assertTrue(user.is_active())

    @unittest.skipIf(
        __SKIP_ALL__, "Deactivate to execute latest created test."
    )
    @unittest.skipUnless(
        __EMAIL_ACTIVATION_TOKEN_ENDPOINTS__,
        "Family of tests for the user activation token via email.",
    )
    def test_confirm_user_activation_invalid(self):
        email = "guest_non_active@xyz.com"

        # Update token for user
        with self.app.app_context():
            user = GwUser.get_by_email(email)
            user.last_activation_token = "DFRgteSDR125kjg"
            user.save()

        activation_token = generate_activation_token(
            SECRET_KEY, SECURITY_PASSWORD_SALT, email
        )

        # Access to endpoint
        res = self.client.get("/confirm/{}".format(activation_token))
        data = json.loads(res.data)

        self.assertEqual(403, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertIn(
            "The confirmation token has expired. Please ask for a new"
            " activation token.",
            data.get("message"),
        )

        # Validate that user is now activated
        with self.app.app_context():
            user = GwUser.get_by_email(email)
            self.assertFalse(user.is_active())

    @unittest.skipIf(
        __SKIP_ALL__, "Deactivate to execute latest created test."
    )
    @unittest.skipUnless(
        __EMAIL_ACTIVATION_TOKEN_ENDPOINTS__,
        "Family of tests for the user activation token via email.",
    )
    def test_resend_activation_token_when_user_anonymous(self):
        payload = {"data": {"email": "user.does.not.exist@gmail.com"}}

        # Access to endpoint
        res = self.client.get("/resend-confirmation", json=payload)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertIn(
            "A new confirmation email has been sent.", data.get("message")
        )

    @unittest.skipIf(
        __SKIP_ALL__, "Deactivate to execute latest created test."
    )
    @unittest.skipUnless(
        __EMAIL_ACTIVATION_TOKEN_ENDPOINTS__,
        "Family of tests for the user activation token via email.",
    )
    def test_resend_activation_token_when_user_login_and_inactive(self):
        email = "guest_non_active@xyz.com"
        password = "1111"

        res = self.login(email, password)
        data = json.loads(res.data)

        self.assertEqual(403, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertNotIn("jwt", data)
        self.assertNotIn("user", data)
        self.assertIn("Account activation required", data.get("message"))

        payload = {"data": {"email": email}}
        # Access to endpoint
        res = self.client.get("/resend-confirmation", json=payload)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertIn(
            "A new confirmation email has been sent.", data.get("message")
        )

        # Check that user is still inactivated
        with self.app.app_context():
            user = GwUser.get_by_email(email)
            self.assertFalse(user.is_active())

    @unittest.skipIf(
        __SKIP_ALL__, "Deactivate to execute latest created test."
    )
    @unittest.skipUnless(
        __EMAIL_ACTIVATION_TOKEN_ENDPOINTS__,
        "Family of tests for the user activation token via email.",
    )
    def test_resend_activation_token_when_user_login_and_active(self):
        email = "guest_active@xyz.com"
        password = "2222"

        res = self.login(email, password)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertIsNotNone(data["data"]["access_token"])
        self.assertIsNotNone(data["data"]["user"])
        self.assertIn("You are now logged in.", data.get("message"))

        payload = {"data": {"email": email}}
        # Access to endpoint
        res = self.client.get("/resend-confirmation", json=payload)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertIn("Your account is already active.", data.get("message"))

        # Validate that user is now activated
        with self.app.app_context():
            user = GwUser.get_by_email(email)
            self.assertTrue(user.is_active())

    @unittest.skipIf(
        __SKIP_ALL__, "Deactivate to execute latest created test."
    )
    @unittest.skipUnless(
        __SIGNUP_ENDPOINTS__, "Family of tests for the signup endpoints."
    )
    def test_signup_new_user(self):
        username = "new_user"
        role = "Guest"
        email = "new_user@example.com"
        password = "password123"

        payload = {
            "username": username,
            "role": role,
            "email": email,
            "password": password,
        }
        # Access to endpoint
        res = self.client.post("/signup", json=payload)
        data = json.loads(res.data)

        self.assertEqual(200, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertIn("You successfully signed up.", data.get("message"))

        # Validate that user is created
        with self.app.app_context():
            user = GwUser.get_by_email(email)
            self.assertIsNotNone(user)
            self.assertFalse(user.is_active())

    @unittest.skipIf(
        __SKIP_ALL__, "Deactivate to execute latest created test."
    )
    @unittest.skipUnless(
        __SIGNUP_ENDPOINTS__, "Family of tests for the signup endpoints."
    )
    def test_signup_when_user_already_exists(self):
        username = "guest_non_active"
        role = "Guest"
        email = "guest_non_active@xyz.com"
        password = "password123"

        payload = {
            "username": username,
            "role": role,
            "email": email,
            "password": password,
        }
        # Access to endpoint
        res = self.client.post("/signup", json=payload)
        data = json.loads(res.data)

        self.assertEqual(422, res.status_code)
        self.assertIn("X-CSRFToken", res.headers)
        self.assertIn(
            "A user already exists for this email !", data.get("message")
        )

        # Validate that user is not created
        with self.app.app_context():
            self.assertEqual(1, GwUser.get_number_of_users_by_email(email))
