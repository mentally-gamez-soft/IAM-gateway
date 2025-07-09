"""Define the routes for the app to send the user activation codes by email."""

import logging

from flask import current_app, jsonify, request
from flask_wtf.csrf import generate_csrf

from config.default import (
    JWT_ENCODING_PARAM_1,
    JWT_EXPIRATION_TIME,
    SECRET_KEY,
    SECURITY_PASSWORD_SALT,
)
from core.auth.generic_encoder_decoder import encode_as_base64
from core.auth.jwt.jwt_handler import decode_jwt
from core.auth.middlewares.validation_token import (
    confirm_activation_token,
    generate_activation_token,
)
from core.common.error_codes import (
    __RESPONSE_STATUS_200,
    __RESPONSE_STATUS_403,
    __RESPONSE_STATUS_422,
)
from core.common.messages import (
    __ACCOUNT_ACTIVATED,
    __ACTIVATION_SUCCESSFUL,
    __DEMAND_RENEW_ACTIVATION,
    __EMAIL_RESENT,
    __GENERIC_ERROR,
    __INVALID_TOKEN_ERROR,
)
from core.common.tools import get_duration_in_minutes
from core.users import users_bp
from core.users.models import GwUser
from core.users.routes import (
    ROUTE_ACTIVATE_USER,
    ROUTE_SEND_CONFIRMATION_EMAIL,
)

logger = logging.getLogger(__name__)


@users_bp.route(ROUTE_ACTIVATE_USER, methods=["GET"])
def confirm_email(token):
    """Define the endpoint for validating and activating a user account.

    Args:
        token (str): The one time use token to activate a user account.

    Returns:
        json: the response.
    """
    json = request.get_json()
    try:
        jwt = json["data"]["jwt"]
        jwt_decoded = decode_jwt(jwt)

        email = confirm_activation_token(
            SECRET_KEY,
            SECURITY_PASSWORD_SALT,
            token,
            expiration=get_duration_in_minutes(duration=JWT_EXPIRATION_TIME),
        )
        user = GwUser.get_by_id(jwt_decoded[JWT_ENCODING_PARAM_1])

        user_activated = False

        if user.email == email:
            user_activated = GwUser.activate_by_id(
                jwt_decoded[JWT_ENCODING_PARAM_1]
            )

        if user_activated.is_active():
            logger.info("The user has been successfully activated.")
            return (
                jsonify(
                    {
                        "data": {
                            "user": encode_as_base64(
                                jwt_decoded[JWT_ENCODING_PARAM_1]
                            ),
                            "jwt": jwt,
                        },
                        "message": __ACTIVATION_SUCCESSFUL,
                        "status": __RESPONSE_STATUS_200,
                        "error": "",
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
                "The user can not be activated. the jwt needs to be renewed."
            )
            return (
                jsonify(
                    {
                        "data": {
                            "user": encode_as_base64(
                                jwt_decoded[JWT_ENCODING_PARAM_1]
                            ),
                            "jwt": jwt,
                        },
                        "error": __INVALID_TOKEN_ERROR,
                        "message": __DEMAND_RENEW_ACTIVATION,
                        "status": __RESPONSE_STATUS_403,
                    }
                ),
                __RESPONSE_STATUS_403,
            )
    except Exception as e:
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


@users_bp.route(
    ROUTE_SEND_CONFIRMATION_EMAIL,
    methods=[
        "GET",
    ],
)
def resend_confirmation_email():
    """Define the endpoint to resend a confirmation email with an activation token.

    Returns:
        json: the response.
    """
    logger.info("The user has ordered a new actiation code.")

    json = request.get_json()
    try:
        jwt = json["data"]["jwt"]
        jwt_decoded = decode_jwt(jwt)

        user = GwUser.get_by_id(jwt_decoded[JWT_ENCODING_PARAM_1])

        if not user.is_active():
            activation_token = generate_activation_token(
                SECRET_KEY, SECURITY_PASSWORD_SALT, user.email
            )
            GwUser.reset_activation_token_by_id(
                jwt_decoded[JWT_ENCODING_PARAM_1], activation_token
            )

            # TODO
            # Send email validation via rabbit MQ
            logger.info("A new activation token was issued.")

            return (
                jsonify(
                    {
                        "data": {
                            "user": encode_as_base64(
                                jwt_decoded[JWT_ENCODING_PARAM_1]
                            ),
                            "jwt": jwt,
                        },
                        "status": __RESPONSE_STATUS_200,
                        "message": __EMAIL_RESENT,
                        "error": "",
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
                        "user": encode_as_base64(
                            jwt_decoded[JWT_ENCODING_PARAM_1]
                        ),
                        "jwt": jwt,
                    },
                    "status": __RESPONSE_STATUS_200,
                    "message": __ACCOUNT_ACTIVATED,
                    "error": "",
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
