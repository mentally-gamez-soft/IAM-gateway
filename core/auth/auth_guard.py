"""Define all the decorators relative to users privileges and rights on the endpoint calls."""

from functools import wraps

from flask import abort, jsonify
from flask_login import current_user

from config.default import JWT_ENCODING_PARAM_1, JWT_ENCODING_PARAM_2
from core.auth.generic_encoder_decoder import (
    decode_as_base64,
    encode_as_base64,
)
from core.auth.jwt.jwt_handler import check_jwt, extract_jwt
from core.common.error_codes import (
    __RESPONSE_STATUS_401,
    __RESPONSE_STATUS_403,
)
from core.common.messages import (
    __ACCESS_DENIED,
    __ACTIVATION_MSG,
    __ACTIVATION_REQUIRED,
    __AUTH_REQUIRED,
    __LOGIN_MSG,
)
from core.users.models import GwUser

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


def auth_guard(role=None):
    """Define the decorator function that will handle the authentication validation via JWT.

    Args:
        role (str, optional): Indicate the role of the user. Defaults to None.
    """

    def wrapper(route_function):
        def decorated_function(*args, **kwargs):
            # Authentication gate
            try:
                user_data = check_jwt()
            except Exception as e:
                return (
                    jsonify(
                        {
                            "error": f"{e}",
                            "message": __LOGIN_MSG,
                            "status": __RESPONSE_STATUS_401,
                            "data": "",
                        }
                    ),
                    __RESPONSE_STATUS_401,
                )

            if not GwUser.is_active_user_by_id(
                decode_as_base64(
                    user_data[encode_as_base64(JWT_ENCODING_PARAM_1)]
                )
            ):
                return (
                    jsonify(
                        {
                            "message": __ACTIVATION_REQUIRED,
                            "status": __RESPONSE_STATUS_401,
                            "data": "",
                            "error": __ACTIVATION_MSG,
                        }
                    ),
                    __RESPONSE_STATUS_401,
                )

            # Authorization gate
            if (
                role
                and role
                not in user_data[encode_as_base64(JWT_ENCODING_PARAM_2)]
                and role
                not in GwUser.get_user_roles_by_id(
                    decode_as_base64(
                        user_data[encode_as_base64(JWT_ENCODING_PARAM_1)]
                    )
                )
            ):
                return (
                    jsonify(
                        {
                            "message": __AUTH_REQUIRED,
                            "status": __RESPONSE_STATUS_403,
                            "data": {
                                "user": user_data[
                                    encode_as_base64(JWT_ENCODING_PARAM_1)
                                ],
                                "jwt": extract_jwt(),
                            },
                            "error": __ACCESS_DENIED,
                        }
                    ),
                    __RESPONSE_STATUS_403,
                )

            # Proceed to original route function
            return route_function(*args, **kwargs)

        decorated_function.__name__ = route_function.__name__
        return decorated_function

    return wrapper
