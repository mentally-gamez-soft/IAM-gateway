"""Define the routes for token refresh and management."""

import logging
from os import environ as env

from flask import current_app, jsonify, request
from flask_login import login_required

from config.default import (
    JWT_ENCODING_PARAM_1,
    JWT_ENCODING_PARAM_2,
    JWT_ENCODING_PARAM_3,
)
from core import limiter
from core.auth.api_endpoint_statistics import count_api_calls
from core.auth.jwt.jwt_handler import generate_token_pair
from core.common.error_codes import (
    __RESPONSE_STATUS_200,
    __RESPONSE_STATUS_400,
    __RESPONSE_STATUS_401,
    __RESPONSE_STATUS_500,
)
from core.common.messages import __LOGIN_SUCCESSFUL
from core.users import users_bp
from core.users.models import GwUser, RefreshToken

logger = logging.getLogger(__name__)

API_TITLE: str = "{}".format(env.get("APP_NAME", "Service-Name"))
API_PREFIX: str = "/{}/api/".format(API_TITLE)
API_VERSION: str = "{}".format(env.get("APP_VERSION", "v1.0.0a"))
BASE_ROUTE: str = "".join([API_PREFIX, API_VERSION])
ROUTE_REFRESH_TOKEN: str = "".join([BASE_ROUTE, "/token/refresh"])


@users_bp.route(ROUTE_REFRESH_TOKEN, methods=["POST"])
@users_bp.route("/token/refresh", methods=["POST"])
@limiter.limit(
    lambda: current_app.config.get("RATE_LIMIT_LOGIN", "1000/minute")
)
@count_api_calls
def refresh_token():
    """Refresh an access token using a refresh token.

    Request body should contain:
    {
        "refresh_token": "<refresh_token_string>"
    }

    Returns:
    {
        "data": {
            "access_token": "<new_access_token>",
            "refresh_token": "<new_refresh_token>",
            "token_type": "Bearer",
            "expires_in": <seconds>
        },
        "status": 200,
        "message": "Token refreshed successfully"
    }

    Raises:
        400: Missing or invalid refresh token
        401: Token expired, revoked, or invalid
        500: Server error
    """
    try:
        # Get refresh token from request body
        data = request.get_json()
        if not data or "refresh_token" not in data:
            logger.warning("Missing refresh token in request")
            return (
                jsonify(
                    {
                        "status": __RESPONSE_STATUS_400,
                        "message": "Missing refresh_token in request body",
                    }
                ),
                __RESPONSE_STATUS_400,
            )

        refresh_token_string = data.get("refresh_token")

        # Hash the refresh token to match against database
        refresh_token_hash = RefreshToken.hash_token(refresh_token_string)

        # Find the refresh token in the database
        refresh_token_record = RefreshToken.get_by_token(refresh_token_hash)

        if not refresh_token_record:
            logger.warning(
                "Refresh token not found in database - possible injection attempt"
            )
            return (
                jsonify(
                    {
                        "status": __RESPONSE_STATUS_401,
                        "message": "Invalid refresh token",
                    }
                ),
                __RESPONSE_STATUS_401,
            )

        # Check if token is expired
        if refresh_token_record.is_expired():
            logger.warning(
                f"Refresh token expired for user {refresh_token_record.user_id}"
            )
            return (
                jsonify(
                    {
                        "status": __RESPONSE_STATUS_401,
                        "message": "Refresh token has expired",
                    }
                ),
                __RESPONSE_STATUS_401,
            )

        # Check if token is revoked
        if refresh_token_record.revoked:
            logger.warning(
                f"Refresh token is revoked for user {refresh_token_record.user_id}"
            )
            return (
                jsonify(
                    {
                        "status": __RESPONSE_STATUS_401,
                        "message": "Refresh token has been revoked",
                    }
                ),
                __RESPONSE_STATUS_401,
            )

        # Check for token reuse (security violation - token family should be revoked)
        if refresh_token_record.replaced_by is not None:
            logger.error(
                f"Token reuse detected for user {refresh_token_record.user_id} "
                f"- family {refresh_token_record.family_id}. "
                "Revoking entire token family due to potential breach."
            )
            # Revoke all tokens in this family for security
            RefreshToken.revoke_family(refresh_token_record.family_id)
            return (
                jsonify(
                    {
                        "status": __RESPONSE_STATUS_401,
                        "message": (
                            "Token has already been used. "
                            "All tokens have been revoked for security."
                        ),
                    }
                ),
                __RESPONSE_STATUS_401,
            )

        # Get the user associated with the token
        user = GwUser.get_by_id(refresh_token_record.user_id)
        if not user:
            logger.error(
                f"User not found for refresh token {refresh_token_record.id}"
            )
            return (
                jsonify(
                    {
                        "status": __RESPONSE_STATUS_401,
                        "message": "User not found",
                    }
                ),
                __RESPONSE_STATUS_401,
            )

        # Revoke the old token and mark it as replaced
        refresh_token_record.revoke()
        refresh_token_record.replaced_by = RefreshToken.hash_token(
            refresh_token_string
        )
        refresh_token_record.save()

        # Generate new token pair with same family ID for tracking
        from datetime import datetime, timedelta

        from application import db
        from config.default import JWT_REFRESH_TOKEN_LIFETIME
        from core.auth.jwt.jwt_handler import (
            generate_jwt,
            generate_refresh_token,
        )

        new_refresh_token_string = generate_refresh_token()
        new_refresh_token_hash = RefreshToken.hash_token(
            new_refresh_token_string
        )

        # Create new token record with same family ID
        new_token_record = RefreshToken(
            token=new_refresh_token_hash,
            user_id=user.id,
            family_id=refresh_token_record.family_id,  # Keep same family
            created_on=datetime.utcnow(),
            expires_on=datetime.utcnow()
            + timedelta(minutes=JWT_REFRESH_TOKEN_LIFETIME),
            revoked=False,
        )

        db.session.add(new_token_record)
        db.session.commit()

        # Generate new access token
        from config.default import JWT_ACCESS_TOKEN_LIFETIME

        access_token = generate_jwt(
            payload={
                JWT_ENCODING_PARAM_1: str(user.id),
                JWT_ENCODING_PARAM_2: GwUser.get_user_roles_by_id(user.id),
                JWT_ENCODING_PARAM_3: user.email,
            },
            lifetime=JWT_ACCESS_TOKEN_LIFETIME,
        )

        expires_in = JWT_ACCESS_TOKEN_LIFETIME * 60  # Convert to seconds

        logger.info(f"Token refreshed successfully for user {user.id}")

        return (
            jsonify(
                {
                    "data": {
                        "access_token": access_token,
                        "refresh_token": new_refresh_token_string,
                        "token_type": "Bearer",
                        "expires_in": expires_in,
                    },
                    "status": __RESPONSE_STATUS_200,
                    "message": "Token refreshed successfully",
                }
            ),
            __RESPONSE_STATUS_200,
        )

    except Exception as e:
        logger.exception(f"Error refreshing token: {e}")
        return (
            jsonify(
                {
                    "status": __RESPONSE_STATUS_500,
                    "message": "An error occurred while refreshing the token",
                }
            ),
            __RESPONSE_STATUS_500,
        )
