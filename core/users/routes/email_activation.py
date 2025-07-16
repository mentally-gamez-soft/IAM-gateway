"""Define the routes for the app to send the user activation codes by email."""

import logging
from os import environ as env

from flask import current_app, jsonify, request
from flask_login import login_required
from flask_wtf.csrf import generate_csrf

from config.default import (
    JWT_ENCODING_PARAM_1,
    JWT_ENCODING_PARAM_2,
    JWT_ENCODING_PARAM_3,
    JWT_EXPIRATION_TIME,
    SECRET_KEY,
    SECURITY_PASSWORD_SALT,
)
from core.auth.api_endpoint_statistics import count_api_calls
from core.auth.auth_guard import authorization_guard
from core.auth.generic_encoder_decoder import encode_as_base64
from core.auth.jwt.jwt_handler import decode_jwt, initiate_session_jwt
from core.auth.middlewares.validation_token import (
    confirm_activation_token,
    generate_activation_token,
)
from core.auth.payload_validator import validate_generic_payload
from core.common.error_codes import (
    __RESPONSE_STATUS_200,
    __RESPONSE_STATUS_401,
    __RESPONSE_STATUS_403,
    __RESPONSE_STATUS_422,
)
from core.common.messages import (
    __ACCESS_DENIED,
    __ACCOUNT_ACTIVATED,
    __ACCOUNT_ALREADY_ACTIVATED,
    __ACTIVATION_SUCCESSFUL,
    __DEMAND_RENEW_ACTIVATION,
    __EMAIL_RESENT,
    __GENERIC_ERROR,
    __INVALID_TOKEN_ERROR,
)
from core.common.tools import get_duration_in_minutes
from core.users import users_bp
from core.users.models import GwUser

logger = logging.getLogger(__name__)

API_TITLE: str = "{}".format(env.get("APP_NAME", "Service-Name"))
API_PREFIX: str = "/{}/api/".format(API_TITLE)
API_VERSION: str = "{}".format(env.get("APP_VERSION", "v1.0.0a"))
BASE_ROUTE: str = "".join([API_PREFIX, API_VERSION])
ROUTE_ACTIVATE_USER: str = "".join([BASE_ROUTE, "/confirm/<token>"])
ROUTE_SEND_CONFIRMATION_EMAIL: str = "".join(
    [BASE_ROUTE, "/resend-confirmation"]
)


@users_bp.route(ROUTE_ACTIVATE_USER, methods=["GET"])
@users_bp.route("/confirm/<token>", methods=["GET"])
def confirm_email(token):
    """Define the endpoint for validating and activating a user account.

    Args:
        token (str): The one time use token to activate a user account.

    Returns:
        json: the response.
    """
    email = confirm_activation_token(
        SECRET_KEY,
        SECURITY_PASSWORD_SALT,
        token,
        expiration=get_duration_in_minutes(duration=int(JWT_EXPIRATION_TIME)),
    )
    user = GwUser.get_by_email(email)
    if not user:
        return (
            jsonify(
                {
                    "message": __ACCESS_DENIED,
                    "status": __RESPONSE_STATUS_401,
                }
            ),
            __RESPONSE_STATUS_401,
            {
                "X-CSRFToken": generate_csrf(
                    secret_key=current_app.config.get("SECRET_KEY")
                )
            },
        )

    if not user.active and user.last_activation_token == token:
        user = GwUser.activate_by_id(user.id)

    jwt = initiate_session_jwt(
        payload={
            JWT_ENCODING_PARAM_1: str(user.id),
            JWT_ENCODING_PARAM_2: user.roles,
            JWT_ENCODING_PARAM_3: user.email,
        },
        lifetime_in_minutes=get_duration_in_minutes(
            duration=int(JWT_EXPIRATION_TIME)
        ),
    )

    if user.is_active():
        logger.info("The user has been successfully activated.")

        return (
            jsonify(
                {
                    "data": {
                        "user": encode_as_base64(str(user.id)),
                        "jwt": jwt,
                    },
                    "message": __ACTIVATION_SUCCESSFUL,
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
    else:
        logger.info(
            "The user can not be activated. the jwt token needs to be renewed."
        )
        return (
            jsonify(
                {
                    "data": {
                        "user": encode_as_base64(str(user.id)),
                        "jwt": jwt,
                    },
                    "message": __DEMAND_RENEW_ACTIVATION,
                    "status": __RESPONSE_STATUS_403,
                }
            ),
            __RESPONSE_STATUS_403,
            {
                "X-CSRFToken": generate_csrf(
                    secret_key=current_app.config.get("SECRET_KEY")
                )
            },
        )


@users_bp.route(
    ROUTE_SEND_CONFIRMATION_EMAIL,
    methods=[
        "GET",
    ],
)
@users_bp.route(
    "/resend-confirmation",
    methods=[
        "GET",
    ],
)
@count_api_calls
def resend_confirmation_email():
    """Define the endpoint to resend a confirmation email with an activation token.

    Returns:
        json: the response.
    """
    logger.info("The user has ordered a new actiation code.")

    json = request.get_json()
    try:
        email = json["data"]["email"]

        user = GwUser.get_by_email(email)
        if not user:
            return (
                jsonify(
                    {
                        "status": __RESPONSE_STATUS_200,
                        "message": __EMAIL_RESENT,
                    }
                ),
                __RESPONSE_STATUS_200,
                {
                    "X-CSRFToken": generate_csrf(
                        secret_key=current_app.config.get("SECRET_KEY")
                    )
                },
            )

        jwt_token = initiate_session_jwt(
            payload={
                JWT_ENCODING_PARAM_1: str(user.id),
                JWT_ENCODING_PARAM_2: user.roles,
                JWT_ENCODING_PARAM_3: user.email,
            },
            lifetime_in_minutes=get_duration_in_minutes(
                duration=int(JWT_EXPIRATION_TIME)
            ),
        )

        if not user.is_active():
            activation_token = generate_activation_token(
                SECRET_KEY, SECURITY_PASSWORD_SALT, user.email
            )
            GwUser.reset_activation_token_by_id(user.id, activation_token)

            # TODO
            # Send email validation via rabbit MQ
            logger.info("A new activation token was issued.")

            return (
                jsonify(
                    {
                        "data": {
                            "user": encode_as_base64(str(user.id)),
                            "jwt": jwt_token,
                        },
                        "status": __RESPONSE_STATUS_200,
                        "message": __EMAIL_RESENT,
                    }
                ),
                __RESPONSE_STATUS_200,
                {
                    "X-CSRFToken": generate_csrf(
                        secret_key=current_app.config.get("SECRET_KEY")
                    )
                },
            )

        logger.info("The user is already activated.")
        return (
            jsonify(
                {
                    "data": {
                        "user": encode_as_base64(str(user.id)),
                        "jwt": jwt_token,
                    },
                    "status": __RESPONSE_STATUS_200,
                    "message": __ACCOUNT_ALREADY_ACTIVATED,
                }
            ),
            __RESPONSE_STATUS_200,
            {
                "X-CSRFToken": generate_csrf(
                    secret_key=current_app.config.get("SECRET_KEY")
                )
            },
        )
    except Exception as e:
        logger.error("An error occured => {}".format(str(e)))
        return (
            jsonify(
                {
                    "data": "",
                    "error": __GENERIC_ERROR,
                    "message": str(e),
                    "status": __RESPONSE_STATUS_422,
                }
            ),
            __RESPONSE_STATUS_422,
        )
