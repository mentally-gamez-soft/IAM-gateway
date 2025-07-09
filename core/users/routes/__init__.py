"""Declare the routes module."""

import uuid
from os import environ as env

from core import login_manager
from core.auth.jwt.jwt_handler import decode_jwt, generate_jwt
from core.users.models import GwUser

API_TITLE: str = "{}".format(env.get("APP_NAME", "Service-Name"))
API_PREFIX: str = "/{}/api/".format(API_TITLE)
API_VERSION: str = "{}".format(env.get("APP_VERSION", "v1.0.0a"))
BASE_ROUTE: str = "".join([API_PREFIX, API_VERSION])
ROUTE_SIGNUP: str = "".join([BASE_ROUTE, "/signup"])
ROUTE_LOGIN: str = "".join([BASE_ROUTE, "/login"])
ROUTE_LOGOUT: str = "".join([BASE_ROUTE, "/logout"])
ROUTE_ACTIVATE_USER: str = "".join([BASE_ROUTE, "/confirm/<token>"])
ROUTE_SEND_CONFIRMATION_EMAIL: str = "".join(
    [BASE_ROUTE, "/resend-confirmation"]
)

import logging

logger = logging.getLogger(__name__)


def initiate_session_jwt(payload, lifetime_in_minutes: int = 30) -> str:
    """Create the jwt from a payload.

    Args:
        payload (dict): the data bond to the jwt.
        lifetime_in_minutes (int, optional): The expiration time in minutes for the token. Defaults to 30 mins.

    Returns:
        str: the jwt token.
    """
    return generate_jwt(payload=payload, lifetime=lifetime_in_minutes)


@login_manager.user_loader
def load_user(user_id: uuid):
    """Load the user session.

    Args:
        user_id (uuid): The id of the user.

    Returns:
        user: an instance for the logged in user.
    """
    logger.info("Try to reload the user from session.")
    return GwUser.get_by_id(user_id)
