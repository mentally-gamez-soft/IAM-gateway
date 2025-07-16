"""Define the routes for the sanity checks."""

import logging
from os import environ as env

from flask import current_app, jsonify, request
from flask_login import login_required
from flask_wtf.csrf import generate_csrf

from core.auth.api_endpoint_statistics import count_api_calls
from core.auth.auth_guard import (
    authorization_guard,
    authorization_guard_artist,
)
from core.auth.payload_validator import validate_generic_payload
from core.common.error_codes import __RESPONSE_STATUS_200
from core.users import users_bp

logger = logging.getLogger(__name__)

API_TITLE: str = "{}".format(env.get("APP_NAME", "Service-Name"))
API_PREFIX: str = "/{}/api/".format(API_TITLE)
API_VERSION: str = "{}".format(env.get("APP_VERSION", "v1.0.0a"))
BASE_ROUTE: str = "".join([API_PREFIX, API_VERSION])


@users_bp.route(BASE_ROUTE, methods=["GET"])
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
        __RESPONSE_STATUS_200,
        {
            "X-CSRFToken": generate_csrf(
                secret_key=current_app.config.get("SECRET_KEY")
            )
        },
    )


@users_bp.route("/protected", methods=["GET", "POST"])
@authorization_guard
@validate_generic_payload
@login_required
@count_api_calls
def protected():
    """Define a test endpoint to check the webservice status with protected routes."""
    logger.info(
        "Call of protected endpoint - headers {}".format(request.headers)
    )
    json = request.get_json()

    return (
        jsonify(
            {
                "data": {
                    "user": json["data"]["user"],
                    "jwt": json["data"]["jwt"],
                },
                "message": (
                    "Welcome to {} service. (You're using the version {})"
                    .format(API_TITLE, API_VERSION)
                ),
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


@users_bp.route("/protected-role", methods=["GET", "POST"])
@authorization_guard_artist
@validate_generic_payload
@login_required
@count_api_calls
def protected_with_role():
    """Define a test endpoint to check the webservice status with protected routes for users with role Artist only."""
    logger.info(
        "Call of protected endpoint - headers {}".format(request.headers)
    )
    json = request.get_json()

    return (
        jsonify(
            {
                "data": {
                    "user": json["data"]["user"],
                    "jwt": json["data"]["jwt"],
                },
                "message": (
                    "Welcome to {} service. (You're using the version {})"
                    .format(API_TITLE, API_VERSION)
                ),
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
