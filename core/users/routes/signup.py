"""Define the routes for user to sign up."""

import logging
from os import environ as env

from flask import current_app, jsonify, request
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
                        "access_token": json["data"]["access_token"],
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

            # TODO: send the email to user for account activation.

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
                        "access_token": jwt_token,
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
