"""Regroup the tools to manage the jwt."""

import arrow
import jwt
from deprecated import deprecated
from flask import request

from config.default import JWT_ALG, SECRET_KEY


def generate_jwt(payload, lifetime=None):
    """Generate a new JWT token, wrapping information provided by payload (dict).

    Args:
        payload (_type_): _description_
        lifetime (int, optional): Lifetime describes (in minutes) how much time the token will be valid. Defaults to None indicating 0 minutes.

    Returns:
        str: The jwt encoded
    """
    if lifetime:
        payload["exp"] = (
            arrow.utcnow()
            .shift(minutes=(0 if not lifetime else lifetime))
            .timestamp()
        )
    return jwt.encode(payload, SECRET_KEY, algorithm=JWT_ALG)


def decode_jwt(token):
    """Retrieve payload information inside of an existent JWT token string.

    Args:
        token (str): JWT encoded token

    Returns:
        json: The payload info if the JWT is valid. Will throw an error if the token is invalid (expired or inconsistent).
    """
    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[
            JWT_ALG,
        ],
    )


@deprecated("No use of authentication bearer header.")
def extract_jwt():
    """Get token from request header and try to get it's payload.

    Raises:
        Exception: The header Authorization is not available in the request.

    Returns:
        str: Bearer auth token.
    """
    # Gets token from request header and tries to get it's payload
    # Will raise errors if token is missing, invalid or expired
    token = request.headers.get("Authorization")
    if not token:
        raise Exception("Missing access token")
    return token.split("Bearer ")[1]


@deprecated("No use of authentication bearer header.")
def check_jwt():
    """Verify a JWT token to ensure authorization.

    Raises:
        Exception: Raise errors if token is missing, invalid or expired

    Returns:
        dict: The payload for the JWT valid token.
    """
    jwt = extract_jwt()
    try:
        return decode_jwt(jwt)
    except Exception as e:
        raise Exception(f"Invalid access token: {e}")


def initiate_session_jwt(payload, lifetime_in_minutes: int = 30) -> str:
    """Create the jwt from a payload.

    Args:
        payload (dict): the data bond to the jwt.
        lifetime_in_minutes (int, optional): The expiration time in minutes for the token. Defaults to 30 mins.

    Returns:
        str: the jwt token.
    """
    return generate_jwt(payload=payload, lifetime=lifetime_in_minutes)
