"""Define the logout route and its behaviour."""

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
)
from core.auth.api_endpoint_statistics import count_api_calls
from core.auth.auth_guard import authorization_guard
from core.auth.jwt.jwt_handler import decode_jwt, initiate_session_jwt
from core.auth.payload_validator import (
    validate_generic_payload,
    validate_role_payload,
)
from core.common.error_codes import (
    __RESPONSE_STATUS_200,
    __RESPONSE_STATUS_401,
    __RESPONSE_STATUS_422,
)
from core.common.messages import __ACCESS_DENIED, __ROLE_ADD_SUCCESSFUL
from core.common.tools import get_duration_in_minutes
from core.users import users_bp
from core.users.models import GwUser, GwUserRole

logger = logging.getLogger(__name__)


@users_bp.route(
    "/role/add",
    methods=[
        "POST",
    ],
)
@authorization_guard
@validate_role_payload
@validate_generic_payload
@login_required
@count_api_calls
def add_role():
    """Allow to add a role to a user.

    Returns:
        Response: the response for this request.
    """
    logger.info(
        "Call of add role endpoint - headers {}".format(request.headers)
    )
    json = request.get_json()

    jwt = json["data"]["access_token"]
    role = json["data"]["role"]

    jwt_decoded = decode_jwt(jwt)
    user = GwUser.get_by_id(jwt_decoded[JWT_ENCODING_PARAM_1])
    new_role = GwUserRole(user.id, role)
    new_role.save()
    new_jwt = initiate_session_jwt(
        payload={
            JWT_ENCODING_PARAM_1: str(user.id),
            JWT_ENCODING_PARAM_2: GwUser.get_user_roles_by_id(user.id),
            JWT_ENCODING_PARAM_3: user.email,
        },
        lifetime_in_minutes=get_duration_in_minutes(
            duration=int(JWT_EXPIRATION_TIME)
        ),
    )

    return (
        jsonify(
            {
                "data": {
                    "user": json["data"]["user"],
                    "access_token": new_jwt,
                },
                "message": __ROLE_ADD_SUCCESSFUL,
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
