"""Define the module for a decorator that validates the standard payloads."""

from functools import wraps

from flask import abort, current_app, jsonify, request
from flask_login import current_user
from flask_wtf.csrf import generate_csrf

from core.common.error_codes import (
    __RESPONSE_STATUS_401,
    __RESPONSE_STATUS_422,
)
from core.common.messages import __ACCESS_DENIED, __PAYLOAD_INVALID


def admin_required(f):
    """Define the decorator to check if a user has admin privileges."""

    @wraps(f)
    def decorated_function(*args, **kws):
        is_admin = getattr(current_user, "is_admin", False)
        if not is_admin:
            abort(401)
        return f(*args, **kws)

    return decorated_function


def validate_generic_payload(f):
    """Define the decorator to check the standard payloads for protected routes."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        json = request.get_json()
        try:
            jwt = json["data"]["access_token"]
        except:
            return (
                jsonify(
                    {
                        "message": __ACCESS_DENIED,
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

        try:
            usr = json["data"]["user"]
        except:
            return (
                jsonify(
                    {
                        "message": __ACCESS_DENIED,
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

        return f(*args, **kwargs)

    return decorated_function


def validate_role_payload(f):
    """Define the decorator to check the standard payloads for protected routes."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        json = request.get_json()
        try:
            rol = json["data"]["role"]
        except:
            return (
                jsonify(
                    {
                        "message": __PAYLOAD_INVALID,
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

        return f(*args, **kwargs)

    return decorated_function
