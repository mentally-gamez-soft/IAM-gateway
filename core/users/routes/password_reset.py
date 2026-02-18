"""Define the routes for password reset functionality."""

import logging
from os import environ as env

from flask import current_app, jsonify, request

from config.default import (
    PASSWORD_RESET_SALT,
    PASSWORD_RESET_TOKEN_EXPIRATION,
    SECRET_KEY,
)
from core import limiter
from core.auth.api_endpoint_statistics import count_api_calls
from core.auth.middlewares.validation_token import (
    confirm_activation_token,
    generate_activation_token,
)
from core.common.error_codes import (
    __RESPONSE_STATUS_200,
    __RESPONSE_STATUS_422,
)
from core.common.messages import __GENERIC_ERROR, __INVALID_TOKEN_ERROR
from core.services.validators.passwords import PasswordValidator
from core.users import users_bp
from core.users.models import GwUser

logger = logging.getLogger(__name__)

API_TITLE: str = "{}".format(env.get("APP_NAME", "Service-Name"))
API_PREFIX: str = "/{}/api/".format(API_TITLE)
API_VERSION: str = "{}".format(env.get("APP_VERSION", "v1.0.0a"))
BASE_ROUTE: str = "".join([API_PREFIX, API_VERSION])
ROUTE_FORGOT_PASSWORD: str = "".join([BASE_ROUTE, "/forgot-password"])
ROUTE_RESET_PASSWORD: str = "".join([BASE_ROUTE, "/reset-password/<token>"])

# Config imports
WS_SCORING_PASSWORD_URL_API = (
    current_app.config.get("WS_SCORING_PASSWORD_URL_API")
    if current_app
    else env.get("WS_SCORING_PASSWORD_URL_API")
)


@users_bp.route(ROUTE_FORGOT_PASSWORD, methods=["POST"])
@users_bp.route("/forgot-password", methods=["POST"])
@limiter.limit(
    lambda: current_app.config.get("RATE_LIMIT_FORGOT_PASSWORD", "3/hour")
)
@count_api_calls
def forgot_password():
    """
    Endpoint to request a password reset.

    Always returns 200 to prevent email enumeration.
    """
    try:
        json = request.get_json()

        if not json:
            json = {}

        # Extract email
        email = json.get("email", "").strip()

        if not email:
            # Return same response for invalid input (prevent enumeration)
            return (
                jsonify(
                    {
                        "message": (
                            "If the email exists in our system, a password reset link has been sent to it."
                        ),
                        "status": __RESPONSE_STATUS_200,
                    }
                ),
                __RESPONSE_STATUS_200,
            )

        # Look up user by email
        user = GwUser.query.filter_by(email=email).first()

        if user:
            # Generate reset token
            token = generate_activation_token(
                SECRET_KEY, PASSWORD_RESET_SALT, email
            )

            # Store token in database
            user.last_password_reset_token = token
            user.save()

            # Send email (delegate to mail service)
            from server.config.mails import send_password_reset_email

            send_password_reset_email(user, token)

            logger.info(
                f"Password reset token generated and email sent for user: {email}"
            )

        # Always return the same response (prevents enumeration)
        return (
            jsonify(
                {
                    "message": (
                        "If the email exists in our system, a password reset link has been sent to it."
                    ),
                    "status": __RESPONSE_STATUS_200,
                }
            ),
            __RESPONSE_STATUS_200,
        )

    except Exception as e:
        logger.error(f"Error in forgot_password endpoint: {str(e)}")
        return (
            jsonify(
                {
                    "message": (
                        "If the email exists in our system, a password reset link has been sent to it."
                    ),
                    "status": __RESPONSE_STATUS_200,
                }
            ),
            __RESPONSE_STATUS_200,
        )


@users_bp.route(ROUTE_RESET_PASSWORD, methods=["POST"])
@users_bp.route("/reset-password/<token>", methods=["POST"])
def reset_password(token):
    """
    Endpoint to reset password using a valid token.

    Returns 200 on success, 422 on validation errors (expired token, weak password, etc).
    """
    try:
        # Validate token and extract email
        email = confirm_activation_token(
            SECRET_KEY,
            PASSWORD_RESET_SALT,
            token,
            expiration=PASSWORD_RESET_TOKEN_EXPIRATION,
        )

        if not email:
            return (
                jsonify(
                    {
                        "message": "Invalid or expired reset token.",
                        "status": __RESPONSE_STATUS_422,
                    }
                ),
                __RESPONSE_STATUS_422,
            )

        # Look up user by email
        user = GwUser.query.filter_by(email=email).first()

        if not user:
            return (
                jsonify(
                    {
                        "message": "User not found.",
                        "status": __RESPONSE_STATUS_422,
                    }
                ),
                __RESPONSE_STATUS_422,
            )

        # Verify token matches the stored token (prevent reuse)
        if user.last_password_reset_token != token:
            return (
                jsonify(
                    {
                        "message": (
                            "Reset token has already been used or is invalid."
                        ),
                        "status": __RESPONSE_STATUS_422,
                    }
                ),
                __RESPONSE_STATUS_422,
            )

        # Validate payload
        json = request.get_json()

        if not json:
            json = {}

        new_password = json.get("password", "").strip()

        if not new_password:
            return (
                jsonify(
                    {
                        "message": "Password is required.",
                        "status": __RESPONSE_STATUS_422,
                    }
                ),
                __RESPONSE_STATUS_422,
            )

        # Validate password strength (using existing password validator)
        global WS_SCORING_PASSWORD_URL_API
        if not WS_SCORING_PASSWORD_URL_API:
            WS_SCORING_PASSWORD_URL_API = current_app.config.get(
                "WS_SCORING_PASSWORD_URL_API"
            )

        is_valid = PasswordValidator.is_valid_password(
            url_api=WS_SCORING_PASSWORD_URL_API,
            password=new_password,
            has_digits=True,
            has_lowercase=True,
            has_spaces=False,
            has_symbols=True,
            has_uppercase=True,
            min_length=10,
            max_length=50,
            min_accepted_score=70,
        )

        if not is_valid:
            return (
                jsonify(
                    {
                        "message": (
                            "Password does not meet strength requirements."
                        ),
                        "status": __RESPONSE_STATUS_422,
                    }
                ),
                __RESPONSE_STATUS_422,
            )

        # Update password
        user.set_password(new_password)

        # Invalidate JWT session
        user.jwt_session_id = None

        # Clear reset token (prevent reuse)
        user.last_password_reset_token = None

        # Save changes
        user.save()

        logger.info(f"Password reset successful for user: {email}")

        return (
            jsonify(
                {
                    "message": (
                        "Password reset successful. Please log in with your new password."
                    ),
                    "status": __RESPONSE_STATUS_200,
                }
            ),
            __RESPONSE_STATUS_200,
        )

    except Exception as e:
        logger.error(f"Error in reset_password endpoint: {str(e)}")

        # Determine the type of error (token-related or other)
        error_message = str(e)

        if "temporary token" in error_message or "max_age" in error_message:
            return (
                jsonify(
                    {
                        "message": (
                            "Reset token has expired. Please request a new one."
                        ),
                        "status": __RESPONSE_STATUS_422,
                    }
                ),
                __RESPONSE_STATUS_422,
            )

        return (
            jsonify(
                {
                    "message": __INVALID_TOKEN_ERROR,
                    "status": __RESPONSE_STATUS_422,
                }
            ),
            __RESPONSE_STATUS_422,
        )
