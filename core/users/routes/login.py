"""Define the routes for a user to log in."""

import logging

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
from core.auth.generic_encoder_decoder import encode_as_base64
from core.auth.middlewares.validation_token import generate_activation_token
from core.common.error_codes import (
    __RESPONSE_STATUS_200,
    __RESPONSE_STATUS_401,
)
from core.common.messages import (
    __ACTIVATION_REQUIRED,
    __LOGIN_SUCCESSFUL,
    __WELCOME_BACK,
)
from core.common.tools import get_duration_in_minutes
from core.users import users_bp
from core.users.forms import LoginForm
from core.users.models import GwUser
from core.users.routes import ROUTE_LOGIN, initiate_session_jwt

logger = logging.getLogger(__name__)


@users_bp.route(ROUTE_LOGIN, methods=["POST"])
def login():
    """Define the form for a user to login."""
    if current_user.is_authenticated:
        logger.info("User is already logged in.")
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

    form = LoginForm(data=request.get_json())
    if form.validate_on_submit():
        user = GwUser.get_by_email(form.email.data)
        if (
            user is not None
            and user.check_password(form.password.data)
            and user.is_active()
        ):
            login_user(user, remember=form.remember_me.data)

            # creation of JWT
            activation_token = generate_activation_token(
                SECRET_KEY, SECURITY_PASSWORD_SALT, user.email
            )
            user.last_activation_token = activation_token
            user.save()

            jwt_token = initiate_session_jwt(
                payload={
                    JWT_ENCODING_PARAM_1: user.id,
                    JWT_ENCODING_PARAM_2: user.roles,
                    JWT_ENCODING_PARAM_3: user.email,
                },
                lifetime_in_minutes=get_duration_in_minutes(
                    duration=JWT_EXPIRATION_TIME
                ),
            )
            logger.info("User logged in successfully.")

            return (
                jsonify(
                    {
                        "data": {
                            "user": encode_as_base64(
                                jwt_token[JWT_ENCODING_PARAM_1]
                            ),
                            "jwt": jwt_token,
                        },
                        "status": __RESPONSE_STATUS_200,
                        "message": __LOGIN_SUCCESSFUL,
                    }
                ),
                __RESPONSE_STATUS_200,
                {
                    "X-CSRFToken": generate_csrf(
                        secret_key=current_app.config.get("SECRET_KEY")
                    )
                },
            )
        elif not user.is_active():
            logger.info("User needs to activate before logging in.")
            return (
                jsonify(
                    {
                        "status": __RESPONSE_STATUS_200,
                        "message": __ACTIVATION_REQUIRED,
                    }
                ),
                __RESPONSE_STATUS_200,
                {
                    "X-CSRFToken": generate_csrf(
                        secret_key=current_app.config.get("SECRET_KEY")
                    )
                },
            )
    else:
        logger.info("User can not log in, credentials are incorrect.")
        if form.email.errors:
            return (
                jsonify(
                    {
                        "status": __RESPONSE_STATUS_401,
                        "message": form.email.errors[0],
                    }
                ),
                __RESPONSE_STATUS_401,
            )
        elif form.password.errors:
            return (
                jsonify(
                    {
                        "status": __RESPONSE_STATUS_401,
                        "message": form.password.errors[0],
                    }
                ),
                __RESPONSE_STATUS_401,
            )
