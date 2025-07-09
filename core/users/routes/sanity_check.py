"""Define the routes for the sanity checks."""

import logging

from flask import current_app, jsonify, request
from flask_login import login_required
from flask_wtf.csrf import generate_csrf

from core.users import users_bp
from core.users.routes import API_TITLE, API_VERSION

logger = logging.getLogger(__name__)


@users_bp.route("/", methods=["GET"])
def default():
    """Define a test endpoint to check the webservice status."""
    logger.info(
        "Call of welcome endpoint - headers {}".format(request.headers)
    )

    return (
        jsonify(
            "Welcome to {} service. (You're using the version {})".format(
                API_TITLE, API_VERSION
            )
        ),
        200,
        {
            "X-CSRFToken": generate_csrf(
                secret_key=current_app.config.get("SECRET_KEY")
            )
        },
    )


@users_bp.route("/protected", methods=["GET"])
@login_required
def protected():
    """Define a test endpoint to check the webservice status with protected routes."""
    logger.info(
        "Call of welcome endpoint - headers {}".format(request.headers)
    )

    return (
        jsonify(
            "Welcome to {} service. (You're using the version {})".format(
                API_TITLE, API_VERSION
            )
        ),
        200,
        {
            "X-CSRFToken": generate_csrf(
                secret_key=current_app.config.get("SECRET_KEY")
            )
        },
    )
