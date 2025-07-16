"""Define the module to record the activity calls of the endpoints."""

from functools import wraps

from flask import request

from core.users.models import StatsApiEndpoints


def count_api_calls(f):
    """Define the decorator to log the calls of the api endpoints."""

    @wraps(f)
    def decorated_function(*args, **kws):
        s_endpoint = ""
        if "logout" in request.url:
            s_endpoint = "logout"
        elif "login" in request.url:
            s_endpoint = "login"
        elif "signup" in request.url:
            s_endpoint = "signup"
        elif "role" in request.url:
            s_endpoint = "role"
        elif "protected" in request.url:
            s_endpoint = "protected"
        elif "resend" in request.url:
            s_endpoint = "request-confirmation-on-web"
        elif "confirm" in request.url:
            s_endpoint = "activate-token-by-email-link"

        StatsApiEndpoints.increment_counter_api_endpoint(s_endpoint)
        return f(*args, **kws)

    return decorated_function
