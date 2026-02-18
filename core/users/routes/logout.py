"""Define the logout route and its behaviour."""

import logging
from os import environ as env

from flask import current_app, jsonify, request
from flask_login import login_required, logout_user
from flask_wtf.csrf import generate_csrf

from config.default import JWT_ENCODING_PARAM_1
from core.auth.api_endpoint_statistics import count_api_calls
from core.auth.auth_guard import authorization_guard
from core.auth.jwt.jwt_handler import decode_jwt
from core.auth.payload_validator import validate_generic_payload
from core.common.error_codes import __RESPONSE_STATUS_200
from core.common.messages import __LOGOUT_SUCCESSFUL
from core.users import users_bp
from core.users.models import GwUser, RefreshToken

logger = logging.getLogger(__name__)

API_TITLE: str = "{}".format(env.get("APP_NAME", "Service-Name"))
API_PREFIX: str = "/{}/api/".format(API_TITLE)
API_VERSION: str = "{}".format(env.get("APP_VERSION", "v1.0.0a"))
BASE_ROUTE: str = "".join([API_PREFIX, API_VERSION])
ROUTE_LOGOUT: str = "".join([BASE_ROUTE, "/logout"])


@users_bp.route(ROUTE_LOGOUT, methods=["POST"])
@users_bp.route("/logout", methods=["POST"])
@authorization_guard
@validate_generic_payload
@login_required
@count_api_calls
def logout():
    """Log a user out.

    Returns:
        Response: the response to the index page.
    """
    json = request.get_json()
    jwt = json["data"]["jwt"]
    jwt_decoded = decode_jwt(jwt)
    user = GwUser.get_by_id(jwt_decoded[JWT_ENCODING_PARAM_1])
    user.jwt_session_id = None
    user.save()

    # Revoke all refresh tokens for the user
    try:
        RefreshToken.revoke_all_for_user(user.id)
        logger.info(f"All refresh tokens revoked for user {user.id}")
    except Exception as e:
        logger.warning(
            f"Error revoking refresh tokens for user {user.id}: {e}"
        )

    logout_user()
    logger.info("User logged out successfully.")
    return (
        jsonify(
            {
                "status": __RESPONSE_STATUS_200,
                "message": __LOGOUT_SUCCESSFUL,
            }
        ),
        __RESPONSE_STATUS_200,
        {
            "X-CSRFToken": generate_csrf(
                secret_key=current_app.config.get("SECRET_KEY")
            )
        },
    )
