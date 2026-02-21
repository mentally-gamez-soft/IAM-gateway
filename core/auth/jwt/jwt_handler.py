"""Regroup the tools to manage the jwt."""

import secrets

import arrow
import jwt
from deprecated import deprecated
from flask import request

from config.default import (
    JWT_ACCESS_TOKEN_LIFETIME,
    JWT_ALG,
    JWT_ENCODING_PARAM_1,
    JWT_REFRESH_TOKEN_LIFETIME,
    SECRET_KEY,
)


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


def generate_refresh_token(length: int = 64) -> str:
    """Generate a secure random refresh token.

    Args:
        length (int, optional): Length of the refresh token. Defaults to 64 characters.

    Returns:
        str: A secure random token string.
    """
    return secrets.token_urlsafe(length)


def generate_token_pair(user_id: str, payload_data: dict) -> dict:
    """Generate both access and refresh tokens for user.

    This function creates an access token (short-lived) and a refresh token
    (long-lived) and stores the refresh token in the database for tracking
    and revocation.

    Args:
        user_id (str): The user's ID (UUID).
        payload_data (dict): Additional payload data to include in the access token
                            (e.g., username, email, roles).

    Returns:
        dict: Dictionary containing:
            - 'access_token': The JWT access token (expires in JWT_ACCESS_TOKEN_LIFETIME)
            - 'refresh_token': The refresh token string (stored in database)
            - 'token_type': 'Bearer'
            - 'expires_in': Seconds until access token expires

    Raises:
        Exception: If the refresh token cannot be saved to the database.
    """
    import uuid
    from datetime import datetime, timedelta

    from core import db
    from core.users.models import RefreshToken

    # Generate access token with short lifetime
    access_payload = {
        "sub": str(user_id),
        JWT_ENCODING_PARAM_1: str(
            user_id
        ),  # backward compat with downstream decoders
        **payload_data,
    }
    access_token = generate_jwt(
        payload=access_payload, lifetime=JWT_ACCESS_TOKEN_LIFETIME
    )

    # Generate refresh token (raw secure string)
    refresh_token_string = generate_refresh_token()

    # Hash the refresh token for storage
    refresh_token_hash = RefreshToken.hash_token(refresh_token_string)

    # Create token family ID for rotation tracking
    family_id = uuid.uuid4()

    # Calculate expiration time
    now = datetime.utcnow()
    expires_on = now + timedelta(minutes=JWT_REFRESH_TOKEN_LIFETIME)

    # Store refresh token in database (token column set after init via attribute)
    refresh_token_record = RefreshToken(
        user_id=user_id,
        expires_on=expires_on,
        family_id=family_id,
    )
    refresh_token_record.token = refresh_token_hash

    try:
        db.session.add(refresh_token_record)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise Exception(f"Failed to save refresh token: {e}")

    # Calculate seconds until access token expires
    expires_in = JWT_ACCESS_TOKEN_LIFETIME * 60  # Convert minutes to seconds

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_string,
        "token_type": "Bearer",
        "expires_in": expires_in,
    }
