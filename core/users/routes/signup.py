"""Define the routes for user to sign up."""

import logging
from os import environ as env

from flask import current_app, jsonify, request, url_for
from flask_login import current_user, login_user
from flask_wtf.csrf import generate_csrf

from config.default import (
    JWT_ENCODING_PARAM_1,
    JWT_ENCODING_PARAM_2,
    JWT_ENCODING_PARAM_3,
    JWT_EXPIRATION_TIME,
    SECRET_KEY,
    SECURITY_PASSWORD_SALT,
)
from core import limiter
from core.auth.api_endpoint_statistics import count_api_calls
from core.auth.generic_encoder_decoder import encode_as_base64
from core.auth.jwt.jwt_handler import initiate_session_jwt
from core.auth.middlewares.validation_token import generate_activation_token
from core.common.credentials_validator import validate_account
from core.common.error_codes import (
    __RESPONSE_STATUS_200,
    __RESPONSE_STATUS_422,
)
from core.common.messages import (
    __SIGNUP_SUCCESSFUL,
    __USER_CREATION_ERROR,
    __USER_WITH_EMAIL_ALREADY_EXISTS,
    __WELCOME_BACK,
)
from core.common.tools import get_duration_in_minutes
from core.users import users_bp
from core.users.forms import SignupForm
from core.users.models import GwUser

logger = logging.getLogger(__name__)

API_TITLE: str = "{}".format(env.get("APP_NAME", "Service-Name"))
API_PREFIX: str = "/{}/api/".format(API_TITLE)
API_VERSION: str = "{}".format(env.get("APP_VERSION", "v1.0.0a"))
BASE_ROUTE: str = "".join([API_PREFIX, API_VERSION])
ROUTE_SIGNUP: str = "".join([BASE_ROUTE, "/signup"])


@users_bp.route(
    ROUTE_SIGNUP,
    methods=("POST",),
)
@users_bp.route(
    "/signup",
    methods=("POST",),
)
@limiter.limit(lambda: current_app.config.get("RATE_LIMIT_SIGNUP", "3/minute"))
@count_api_calls
def signup():
    """Define the signup endpoint."""
    if current_user.is_authenticated:
        logger.info("The user is already logged in.")
        json = request.get_json()
        return (
            jsonify(
                {
                    "data": {
                        "user": json["data"]["user"],
                        "jwt": json["data"]["jwt"],
                    },
                    "message": __WELCOME_BACK,
                    "status": __RESPONSE_STATUS_200,
                }
            ),
            __RESPONSE_STATUS_200,
            {
                "X-CSRFToken": generate_csrf(
                    secret_key=current_app.config.get("SECRET_KEY")
                )
            },
        )

    form = SignupForm(data=request.get_json())
    error = None

    username = form.username.data
    email = form.email.data
    password = form.password.data
    role = form.role.data
    check_account = validate_account(
        username=username, email=email, password=password
    )

    if not check_account["status"]:
        logger.info(
            "Creation of the account user impossible => {}.".format(
                check_account["message"]
            )
        )
        return (
            jsonify(
                {
                    "error": __USER_CREATION_ERROR,
                    "message": check_account["message"],
                    "status": check_account["status-code"],
                }
            ),
            check_account["status-code"],
            {
                "X-CSRFToken": generate_csrf(
                    secret_key=current_app.config.get("SECRET_KEY")
                )
            },
        )

    if not form.validate():
        logger.info(
            "Creation of the account user impossible, inputs are incorrect"
            " => {}".format(form.errors)
        )
        if form.username.errors:
            return (
                jsonify(
                    {
                        "message": form.username.errors[0],
                        "status": __RESPONSE_STATUS_422,
                    }
                ),
                __RESPONSE_STATUS_422,
                {
                    "X-CSRFToken": generate_csrf(
                        secret_key=current_app.config.get("SECRET_KEY")
                    )
                },
            )
        elif form.email.errors:
            return (
                jsonify(
                    {
                        "message": form.email.errors[0],
                        "status": __RESPONSE_STATUS_422,
                    }
                ),
                __RESPONSE_STATUS_422,
                {
                    "X-CSRFToken": generate_csrf(
                        secret_key=current_app.config.get("SECRET_KEY")
                    )
                },
            )
        elif form.password.errors:
            return (
                jsonify(
                    {
                        "message": form.password.errors[0],
                        "status": __RESPONSE_STATUS_422,
                    }
                ),
                __RESPONSE_STATUS_422,
                {
                    "X-CSRFToken": generate_csrf(
                        secret_key=current_app.config.get("SECRET_KEY")
                    )
                },
            )
        elif form.role.errors:
            return (
                jsonify(
                    {
                        "message": form.role.errors[0],
                        "status": __RESPONSE_STATUS_422,
                    }
                ),
                __RESPONSE_STATUS_422,
                {
                    "X-CSRFToken": generate_csrf(
                        secret_key=current_app.config.get("SECRET_KEY")
                    )
                },
            )

    elif form.validate():
        # Check that a user with same email dose not already exist
        user = GwUser.get_by_email(email)
        if user:
            logger.info(
                "Creation of the account user impossible: email already"
                " exists."
            )
            return (
                jsonify(
                    {
                        "message": __USER_WITH_EMAIL_ALREADY_EXISTS,
                        "status": __RESPONSE_STATUS_422,
                    }
                ),
                __RESPONSE_STATUS_422,
                {
                    "X-CSRFToken": generate_csrf(
                        secret_key=current_app.config.get("SECRET_KEY")
                    )
                },
            )
        else:
            user = GwUser(username=username, email=check_account["email"])
            user.set_password(password)
            user.save()

            GwUser.add_role_to_user_by_id(user.id, role)

            login_user(user, remember=True)

            # creation of JWT
            activation_token = generate_activation_token(
                SECRET_KEY, SECURITY_PASSWORD_SALT, user.email
            )
            user.last_activation_token = activation_token

            # Dispatch account-activation email asynchronously when enabled.
            if current_app.config.get("USE_ASYNC_EMAIL", True):
                try:
                    from core.tasks.email_tasks import send_email_task

                    activation_url = url_for(
                        "users.confirm_email",
                        token=activation_token,
                        _external=True,
                    )
                    html_body = (
                        "<html><body style='font-family:Arial,sans-serif;"
                        "line-height:1.6;color:#333;'>"
                        "<div style='max-width:600px;margin:0 auto;padding:"
                        "20px;border:1px solid #ddd;border-radius:5px;'>"
                        f"<h2>Welcome, {user.username}!</h2>"
                        "<p>Thank you for creating an account. Please click "
                        "the button below to activate it.</p>"
                        "<p style='text-align:center;margin:30px 0;'>"
                        f"<a href='{activation_url}' style='background-color:"
                        "#3498db;color:white;padding:12px 30px;text-decoration"
                        ":none;border-radius:5px;display:inline-block;'>"
                        "Activate Account</a></p>"
                        "<p>Or copy this link:</p>"
                        f"<p style='background-color:#f4f4f4;padding:10px;"
                        "border-radius:3px;word-break:break-all;'>"
                        f"{activation_url}</p>"
                        "<p style='color:#7f8c8d;font-size:12px;'>"
                        "Best regards,<br>The IAM Gateway Team</p>"
                        "</div></body></html>"
                    )
                    text_body = (
                        f"Welcome, {user.username}!\n\n"
                        "Please activate your account by visiting:\n"
                        f"{activation_url}\n\n"
                        "Best regards,\nThe IAM Gateway Team"
                    )
                    send_email_task.delay(
                        to=user.email,
                        subject="Activate your IAM Gateway account",
                        body=text_body,
                        html_body=html_body,
                    )
                    logger.info("Activation email queued for %s", user.email)
                except Exception as exc:
                    logger.error(
                        "Failed to queue activation email for %s: %s",
                        user.email,
                        str(exc),
                    )

            jwt_token = initiate_session_jwt(
                payload={
                    JWT_ENCODING_PARAM_1: str(user.id),
                    JWT_ENCODING_PARAM_2: GwUser.get_user_roles_by_id(user.id),
                    JWT_ENCODING_PARAM_3: user.email,
                },
                lifetime_in_minutes=get_duration_in_minutes(
                    duration=int(JWT_EXPIRATION_TIME)
                ),
            )
            user.jwt_session_id = jwt_token
            user.save()
            logger.info("New user created successfully.")

        return (
            jsonify(
                {
                    "data": {
                        "user": encode_as_base64(str(user.id)),
                        "jwt": jwt_token,
                    },
                    "status": __RESPONSE_STATUS_200,
                    "message": __SIGNUP_SUCCESSFUL,
                }
            ),
            __RESPONSE_STATUS_200,
            {
                "X-CSRFToken": generate_csrf(
                    secret_key=current_app.config.get("SECRET_KEY")
                )
            },
        )
