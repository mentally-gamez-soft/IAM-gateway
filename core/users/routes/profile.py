"""Define the routes for user profile management (US-011).

Endpoints:
    GET  /profile  — retrieve the authenticated user's profile.
    PUT  /profile  — update mutable profile fields.
"""

import logging
from os import environ as env

from flask import current_app, jsonify, request
from flask_login import login_required
from flask_wtf.csrf import generate_csrf

from config.default import JWT_ENCODING_PARAM_1
from core.auth.api_endpoint_statistics import count_api_calls
from core.auth.auth_guard import authorization_guard
from core.auth.generic_encoder_decoder import decode_as_base64
from core.auth.jwt.jwt_handler import decode_jwt
from core.auth.payload_validator import validate_generic_payload
from core.common.error_codes import (
    __RESPONSE_STATUS_200,
    __RESPONSE_STATUS_400,
    __RESPONSE_STATUS_422,
)
from core.common.messages import (
    __PROFILE_AVATAR_URL_TOO_LONG,
    __PROFILE_DISPLAY_NAME_TOO_LONG,
    __PROFILE_FIELD_PROTECTED,
    __PROFILE_GET_SUCCESSFUL,
    __PROFILE_LANGUAGE_INVALID,
    __PROFILE_TIMEZONE_INVALID,
    __PROFILE_UPDATE_SUCCESSFUL,
)
from core.users import users_bp
from core.users.models import GwUser

logger = logging.getLogger(__name__)

API_TITLE: str = "{}".format(env.get("APP_NAME", "Service-Name"))
API_PREFIX: str = "/{}/api/".format(API_TITLE)
API_VERSION: str = "{}".format(env.get("APP_VERSION", "v1.0.0a"))
BASE_ROUTE: str = "".join([API_PREFIX, API_VERSION])
ROUTE_PROFILE: str = "".join([BASE_ROUTE, "/profile"])

# Fields that can never be modified via the profile endpoint.
_PROTECTED_FIELDS = {
    "email",
    "username",
    "password",
    "roles",
    "is_admin",
    "id",
}

# Allowed mutable profile fields.
_MUTABLE_FIELDS = {
    "display_name",
    "avatar_url",
    "bio",
    "language_preference",
    "timezone",
}


def _get_current_user_from_request(json: dict) -> "GwUser | None":
    """Extract and return the GwUser from the standard request payload.

    The route accepts both the legacy ``data.jwt`` field and the newer
    ``data.access_token`` field to maintain flexibility.

    Args:
        json (dict): Parsed request JSON.

    Returns:
        GwUser | None: The user instance, or None if not found.
    """
    try:
        # Support both legacy "jwt" key and new "access_token" key.
        token = json["data"].get("access_token") or json["data"].get("jwt")
        decoded = decode_jwt(token)
        user_id = decoded[JWT_ENCODING_PARAM_1]
        return GwUser.get_by_id(user_id)
    except Exception:
        # Fallback: resolve user from the base64-encoded "user" field.
        try:
            encoded_user = json["data"]["user"]
            return GwUser.get_by_id(decode_as_base64(encoded_user))
        except Exception:
            return None


def _validate_profile_payload(data: dict) -> tuple[dict | None, str | None]:
    """Validate the mutable profile fields supplied in a PUT request.

    Args:
        data (dict): The dictionary of fields to update.

    Returns:
        tuple: (cleaned_data, error_message). If valid, error_message is None.
    """
    # Reject any attempt to update protected fields.
    attempted_protected = _PROTECTED_FIELDS.intersection(data.keys())
    if attempted_protected:
        return None, __PROFILE_FIELD_PROTECTED

    # Validate individual field constraints.
    if "display_name" in data and len(data["display_name"] or "") > 80:
        return None, __PROFILE_DISPLAY_NAME_TOO_LONG

    if "avatar_url" in data and len(data["avatar_url"] or "") > 255:
        return None, __PROFILE_AVATAR_URL_TOO_LONG

    if "language_preference" in data:
        lp = data["language_preference"] or ""
        if not (2 <= len(lp) <= 5):
            return None, __PROFILE_LANGUAGE_INVALID

    if "timezone" in data and len(data["timezone"] or "") > 50:
        return None, __PROFILE_TIMEZONE_INVALID

    # Strip out any unknown keys so only mutable fields reach the model.
    cleaned = {k: v for k, v in data.items() if k in _MUTABLE_FIELDS}
    return cleaned, None


# ---------------------------------------------------------------------------
# GET /profile
# ---------------------------------------------------------------------------


@users_bp.route(ROUTE_PROFILE, methods=["GET"])
@users_bp.route("/profile", methods=["GET"])
@authorization_guard
@validate_generic_payload
@login_required
@count_api_calls
def get_profile():
    """Return the authenticated user's profile.

    Returns:
        Response: JSON profile data with HTTP 200, or 400/422 on error.
    """
    json = request.get_json()
    user = _get_current_user_from_request(json)

    if not user:
        logger.warning(
            "get_profile: could not resolve user from request payload."
        )
        return (
            jsonify(
                {
                    "message": "User not found.",
                    "status": __RESPONSE_STATUS_422,
                }
            ),
            __RESPONSE_STATUS_422,
            {
                "X-CSRFToken": generate_csrf(
                    secret_key=current_app.config.get("SECRET_KEY")
                )
            },
        )

    logger.info("Profile retrieved for user %s.", user.id)
    return (
        jsonify(
            {
                "data": {"profile": user.to_profile_dict()},
                "message": __PROFILE_GET_SUCCESSFUL,
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


# ---------------------------------------------------------------------------
# PUT /profile
# ---------------------------------------------------------------------------


@users_bp.route(ROUTE_PROFILE, methods=["PUT"])
@users_bp.route("/profile", methods=["PUT"])
@authorization_guard
@validate_generic_payload
@login_required
@count_api_calls
def update_profile():
    """Update mutable fields on the authenticated user's profile.

    Accepts a JSON body of the form::

        {
            "data": {
                "jwt": "<token>",
                "user": "<base64-user-id>",
                "profile": {
                    "display_name": "...",
                    "avatar_url": "...",
                    "bio": "...",
                    "language_preference": "en",
                    "timezone": "UTC"
                }
            }
        }

    Protected fields (email, username, roles, etc.) are rejected if present.

    Returns:
        Response: Updated profile JSON with HTTP 200, or 400/422 on error.
    """
    json = request.get_json()
    user = _get_current_user_from_request(json)

    if not user:
        logger.warning(
            "update_profile: could not resolve user from request payload."
        )
        return (
            jsonify(
                {
                    "message": "User not found.",
                    "status": __RESPONSE_STATUS_422,
                }
            ),
            __RESPONSE_STATUS_422,
            {
                "X-CSRFToken": generate_csrf(
                    secret_key=current_app.config.get("SECRET_KEY")
                )
            },
        )

    # Extract the profile update data — default to empty dict if not provided.
    try:
        profile_data = json["data"].get("profile", {}) or {}
    except Exception:
        profile_data = {}

    cleaned_data, error_msg = _validate_profile_payload(profile_data)
    if error_msg:
        logger.warning(
            "update_profile: validation error for user %s: %s",
            user.id,
            error_msg,
        )
        return (
            jsonify(
                {
                    "message": error_msg,
                    "status": __RESPONSE_STATUS_400,
                }
            ),
            __RESPONSE_STATUS_400,
            {
                "X-CSRFToken": generate_csrf(
                    secret_key=current_app.config.get("SECRET_KEY")
                )
            },
        )

    user.update_profile(cleaned_data)
    logger.info("Profile updated for user %s.", user.id)

    return (
        jsonify(
            {
                "data": {"profile": user.to_profile_dict()},
                "message": __PROFILE_UPDATE_SUCCESSFUL,
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
