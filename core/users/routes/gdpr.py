"""Define the GDPR compliance routes: data export, account deletion, and consent management."""

import logging
from os import environ as env

from flask import current_app, jsonify, request
from flask_login import login_required, logout_user
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
    __RESPONSE_STATUS_401,
    __RESPONSE_STATUS_403,
    __RESPONSE_STATUS_409,
)
from core.common.messages import (
    __ACCESS_DENIED,
    __ACCOUNT_ALREADY_DELETED,
    __ACCOUNT_DELETE_CONFIRM_REQUIRED,
    __ACCOUNT_DELETE_PASSWORD_INVALID,
    __ACCOUNT_DELETE_SUCCESSFUL,
    __CONSENT_RETRIEVE_SUCCESSFUL,
    __CONSENT_UPDATE_SUCCESSFUL,
    __DATA_EXPORT_SUCCESSFUL,
)
from core.users import users_bp
from core.users.models import GwUser, RefreshToken, UserConsent

logger = logging.getLogger(__name__)

API_TITLE: str = "{}".format(env.get("APP_NAME", "Service-Name"))
API_PREFIX: str = "/{}/api/".format(API_TITLE)
API_VERSION: str = "{}".format(env.get("APP_VERSION", "v1.0.0a"))
BASE_ROUTE: str = "".join([API_PREFIX, API_VERSION])

ROUTE_USER_DATA: str = "".join([BASE_ROUTE, "/user/data"])
ROUTE_USER_ACCOUNT: str = "".join([BASE_ROUTE, "/user/account"])
ROUTE_USER_CONSENT: str = "".join([BASE_ROUTE, "/user/consent"])


def _get_user_from_request() -> GwUser:
    """Extract and return the GwUser instance from the request payload.

    Returns:
        GwUser: The authenticated user instance.
    """
    json = request.get_json()
    token = json["data"].get("jwt") or json["data"].get("access_token")
    decoded = decode_jwt(token)
    return GwUser.get_by_id(decoded[JWT_ENCODING_PARAM_1])


# ---------------------------------------------------------------------------
# TASK-012-1 — GET /user/data (GDPR data export)
# ---------------------------------------------------------------------------


@users_bp.route(ROUTE_USER_DATA, methods=["GET", "POST"])
@users_bp.route("/user/data", methods=["GET", "POST"])
@authorization_guard
@validate_generic_payload
@login_required
@count_api_calls
def user_data_export():
    """Export all personal data for the authenticated user (GDPR Article 20).

    Returns:
        Response: A JSON payload containing all user-owned data.
    """
    logger.info(
        "GDPR data export requested - headers {}".format(request.headers)
    )
    user = _get_user_from_request()
    logger.info("GDPR data export completed for user_id={}".format(user.id))

    return (
        jsonify(
            {
                "data": user.export_data(),
                "message": __DATA_EXPORT_SUCCESSFUL,
                "status": __RESPONSE_STATUS_200,
            }
        ),
        __RESPONSE_STATUS_200,
        {
            "Content-Type": "application/json",
            "X-CSRFToken": generate_csrf(
                secret_key=current_app.config.get("SECRET_KEY")
            ),
        },
    )


# ---------------------------------------------------------------------------
# TASK-012-2 — DELETE /user/account (soft-delete + anonymize)
# ---------------------------------------------------------------------------


@users_bp.route(ROUTE_USER_ACCOUNT, methods=["DELETE"])
@users_bp.route("/user/account", methods=["DELETE"])
@authorization_guard
@validate_generic_payload
@login_required
@count_api_calls
def delete_account():
    """Soft-delete and anonymize the authenticated user's account (GDPR right to erasure).

    Expected payload::

        {
            "data": {
                "user": "<base64 user_id>",
                "access_token": "<jwt>",
                "confirm": true,
                "password": "<current password>"
            }
        }

    Returns:
        Response: 200 on success, 400/401/403/409 on failure.
    """
    logger.info(
        "GDPR account deletion requested - headers {}".format(request.headers)
    )
    json = request.get_json()
    data = json.get("data", {})

    # Require explicit confirmation flag
    if not data.get("confirm", False):
        logger.warning("Account deletion attempted without confirm=True.")
        return (
            jsonify(
                {
                    "message": __ACCOUNT_DELETE_CONFIRM_REQUIRED,
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

    user = _get_user_from_request()

    # Guard: already deleted?
    if user.deleted:
        logger.warning(
            "Double-deletion attempt for user_id={}".format(user.id)
        )
        return (
            jsonify(
                {
                    "message": __ACCOUNT_ALREADY_DELETED,
                    "status": __RESPONSE_STATUS_409,
                }
            ),
            __RESPONSE_STATUS_409,
            {
                "X-CSRFToken": generate_csrf(
                    secret_key=current_app.config.get("SECRET_KEY")
                )
            },
        )

    # Validate password
    password = data.get("password", "")
    if not password or not user.check_password(password):
        logger.warning(
            "Account deletion failed due to incorrect password for user_id={}".format(
                user.id
            )
        )
        return (
            jsonify(
                {
                    "message": __ACCOUNT_DELETE_PASSWORD_INVALID,
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

    # Revoke all refresh tokens
    try:
        RefreshToken.revoke_all_for_user(user.id)
    except Exception as exc:
        logger.error(
            "Error revoking refresh tokens during deletion for user_id={}: {}".format(
                user.id, exc
            )
        )

    # Soft-delete and anonymize
    user.soft_delete_and_anonymize()
    logout_user()
    logger.info(
        "User account soft-deleted and anonymized successfully for user_id={}".format(
            user.id
        )
    )

    return (
        jsonify(
            {
                "message": __ACCOUNT_DELETE_SUCCESSFUL,
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
# TASK-012-3 — GET /user/consent and PUT /user/consent
# ---------------------------------------------------------------------------


@users_bp.route(ROUTE_USER_CONSENT, methods=["GET", "POST"])
@users_bp.route("/user/consent", methods=["GET", "POST"])
@authorization_guard
@validate_generic_payload
@login_required
@count_api_calls
def get_consent():
    """Return all current consent preferences for the authenticated user.

    Returns:
        Response: A JSON payload listing all consent records.
    """
    logger.info(
        "GDPR consent retrieval requested - headers {}".format(request.headers)
    )
    user = _get_user_from_request()
    consents = UserConsent.get_all_for_user(user.id)
    consent_list = [
        {
            "consent_type": c.consent_type,
            "granted": c.granted,
            "granted_at": c.granted_at.isoformat() if c.granted_at else None,
            "revoked_at": c.revoked_at.isoformat() if c.revoked_at else None,
            "ip_address": c.ip_address,
        }
        for c in consents
    ]

    return (
        jsonify(
            {
                "data": {
                    "consent_given": user.consent_given,
                    "consent_at": (
                        user.consent_at.isoformat()
                        if user.consent_at
                        else None
                    ),
                    "consents": consent_list,
                },
                "message": __CONSENT_RETRIEVE_SUCCESSFUL,
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


@users_bp.route(ROUTE_USER_CONSENT, methods=["PUT"])
@users_bp.route("/user/consent", methods=["PUT"])
@authorization_guard
@validate_generic_payload
@login_required
@count_api_calls
def update_consent():
    """Update GDPR consent preferences for the authenticated user.

    Expected payload::

        {
            "data": {
                "user": "<base64 user_id>",
                "access_token": "<jwt>",
                "consent_given": true,
                "consents": [
                    {"consent_type": "marketing", "granted": true},
                    {"consent_type": "analytics", "granted": false}
                ]
            }
        }

    Returns:
        Response: 200 on success, 400 on missing payload.
    """
    logger.info(
        "GDPR consent update requested - headers {}".format(request.headers)
    )
    json = request.get_json()
    data = json.get("data", {})

    if "consent_given" not in data:
        return (
            jsonify(
                {
                    "message": "Field 'consent_given' is required.",
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

    user = _get_user_from_request()
    ip_address = request.remote_addr
    consent_given = bool(data["consent_given"])

    # Update top-level consent flag on the user
    user.update_consent(consent_given=consent_given, ip_address=ip_address)

    # Upsert per-type consent records if provided
    per_type_consents = data.get("consents", [])
    for entry in per_type_consents:
        consent_type = entry.get("consent_type")
        granted = bool(entry.get("granted", False))
        if consent_type:
            UserConsent.upsert(
                user_id=user.id,
                consent_type=consent_type,
                granted=granted,
                ip_address=ip_address,
            )

    logger.info(
        "GDPR consent updated for user_id={} consent_given={}".format(
            user.id, consent_given
        )
    )

    return (
        jsonify(
            {
                "data": {
                    "consent_given": user.consent_given,
                    "consent_at": (
                        user.consent_at.isoformat()
                        if user.consent_at
                        else None
                    ),
                },
                "message": __CONSENT_UPDATE_SUCCESSFUL,
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
