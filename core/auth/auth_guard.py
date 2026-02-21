"""Define all the decorators relative to users privileges and rights on the endpoint calls."""

import logging
from functools import partial, update_wrapper, wraps

from flask import abort, current_app, jsonify, request
from flask_login import current_user
from flask_wtf.csrf import generate_csrf

from config.default import JWT_ENCODING_PARAM_1, JWT_ENCODING_PARAM_2
from core.auth.generic_encoder_decoder import decode_as_base64
from core.common.error_codes import (
    __RESPONSE_STATUS_401,
    __RESPONSE_STATUS_403,
)
from core.common.messages import (
    __ACCESS_DENIED,
    __ACTIVATION_REQUIRED,
    __AUTH_REQUIRED,
)
from core.users.models import GwUser

logger = logging.getLogger(__name__)

JWT_ENCODING_PARAM_1 = JWT_ENCODING_PARAM_1
JWT_ENCODING_PARAM_2 = JWT_ENCODING_PARAM_2


def admin_required(f):
    """Define the decorator to check if a user has admin privileges."""

    @wraps(f)
    def decorated_function(*args, **kws):
        is_admin = getattr(current_user, "is_admin", False)
        if not is_admin:
            abort(401)
        return f(*args, **kws)

    return decorated_function


# https://stackoverflow.com/questions/5929107/decorators-with-parameters
def authorization_guard(f, role=None):
    """Define the decorator function that will handle the authorization access to an endpoint according to the role of the user.

    Args:
        role (str, optional): Indicate the role of the user. Defaults to None.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        json = request.get_json()

        # Authentication gate — accept both legacy "jwt" and new "access_token".
        try:
            jwt = json["data"].get("jwt") or json["data"].get("access_token")
            if not jwt:
                raise KeyError("No token found in request data")
            user = json["data"]["user"]
        except Exception as e:
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

        if not GwUser.get_by_id(decode_as_base64(user)):
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

        if not GwUser.is_active_user_by_id(decode_as_base64(user)):
            return (
                jsonify(
                    {
                        "message": __ACTIVATION_REQUIRED,
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

        # Authorization gate
        if role and role not in GwUser.get_user_roles_by_id(
            decode_as_base64(user)
        ):
            logger.error(
                "The role {} is not in the list {}".format(
                    role, GwUser.get_user_roles_by_id(decode_as_base64(user))
                )
            )
            return (
                jsonify(
                    {
                        "message": __AUTH_REQUIRED,
                        "status": __RESPONSE_STATUS_403,
                        "data": {
                            "user": user,
                            "jwt": jwt,
                        },
                    }
                ),
                __RESPONSE_STATUS_403,
                {
                    "X-CSRFToken": generate_csrf(
                        secret_key=current_app.config.get("SECRET_KEY")
                    )
                },
            )

        # Proceed to original route function
        return f(*args, **kwargs)

    return decorated_function


authorization_guard_artist = partial(authorization_guard, role="Artist")
authorization_guard_blogger = partial(authorization_guard, role="Blogger")
