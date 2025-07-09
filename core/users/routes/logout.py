"""Define the logout route and its behaviour."""

import logging

from flask import current_app, jsonify, request
from flask_login import login_required, logout_user
from flask_wtf.csrf import generate_csrf

from config.default import JWT_ENCODING_PARAM_1
from core.auth.jwt.jwt_handler import decode_jwt
from core.common.error_codes import __RESPONSE_STATUS_200
from core.common.messages import __LOGOUT_SUCCESSFUL
from core.users import users_bp
from core.users.models import GwUser
from core.users.routes import ROUTE_LOGOUT

logger = logging.getLogger(__name__)


@users_bp.route(ROUTE_LOGOUT, methods=["POST"])
@login_required
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
