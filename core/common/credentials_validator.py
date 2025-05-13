"""Define the module to validate users inputs."""

from config.default import (
    RULE_PASSWORD_MAX_LENGTH,
    RULE_PASSWORD_MIN_LENGTH,
    RULE_PASSWORD_MIN_STRENGTH_SCORE,
    RULE_PASSWORD_WITH_DIGITS,
    RULE_PASSWORD_WITH_LOWERCASE,
    RULE_PASSWORD_WITH_SPACES,
    RULE_PASSWORD_WITH_SYMBOLS,
    RULE_PASSWORD_WITH_UPPERCASE,
    RULE_USERNAME_MAX_CHAR,
    WS_SCORING_PASSWORD_URL_API,
)
from core.common.error_codes import (
    __RESPONSE_STATUS_200,
    __RESPONSE_STATUS_422,
)
from core.common.messages import __EMAIL_INVALID, __USERNAME_INVALID
from core.services.validators.emails import EmailValidator
from core.services.validators.passwords import PasswordValidator
from core.services.validators.usernames import UsernameValidator


def __valid_email(email: str) -> dict:
    return EmailValidator.is_valid_email(email)


def __valid_username(username: str) -> bool:
    return UsernameValidator.is_valid_username(
        username, RULE_USERNAME_MAX_CHAR
    )


def __valid_password(password: str) -> dict:
    url_api = WS_SCORING_PASSWORD_URL_API

    has_digits = RULE_PASSWORD_WITH_DIGITS
    has_lowercase = RULE_PASSWORD_WITH_LOWERCASE
    has_spaces = RULE_PASSWORD_WITH_SPACES
    has_symbols = RULE_PASSWORD_WITH_SYMBOLS
    has_uppercase = RULE_PASSWORD_WITH_UPPERCASE
    min_length = RULE_PASSWORD_MIN_LENGTH
    max_length = RULE_PASSWORD_MAX_LENGTH
    min_accepted_score = RULE_PASSWORD_MIN_STRENGTH_SCORE
    # TODO add the resilient pattern for external API calls.
    return PasswordValidator.is_valid_password(
        url_api=url_api,
        password=password,
        has_digits=has_digits,
        has_lowercase=has_lowercase,
        has_spaces=has_spaces,
        has_symbols=has_symbols,
        has_uppercase=has_uppercase,
        min_length=min_length,
        max_length=max_length,
        min_accepted_score=min_accepted_score,
    )


def validate_account(username: str, email: str, password: str) -> dict:
    """Validate a user account according to the rules implemented for usernames, passowrds and emails.

    Args:
        username (str): input user name
        email (str): input email of the user
        password (str): input password

    Returns:
        dict: indicate the response status code, a status and a message.
    """
    # Validation of username
    if not __valid_username(username):
        return {
            "status": False,
            "message": __USERNAME_INVALID,
            "status-code": __RESPONSE_STATUS_422,
        }

    # Validation of email
    email_check = __valid_email(email)
    if not email_check["status"]:
        return {
            "status": False,
            "message": __EMAIL_INVALID,
            "status-code": __RESPONSE_STATUS_422,
        }
    email = email_check["email"]

    # Validation of the input password: format + strength
    password_score = __valid_password(password)
    if not password_score["status"]:
        return {
            "status": False,
            "message": password_score["message"],
            "status-code": __RESPONSE_STATUS_422,
        }

    return {
        "email": email,
        "status": True,
        "status-code": __RESPONSE_STATUS_200,
    }
