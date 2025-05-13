"""Set of tools for the validation/activation of a user."""

from itsdangerous import URLSafeTimedSerializer


def generate_activation_token(
    application_secret_key, application_password_salt, email
):
    """Create the one use token for the user to activate his/her account.

    Args:
        application_secret_key (str): The secret key of the application.
        application_password_salt (str): secret key specific for managing the activation token.
        email (str): The email of the user.

    Returns:
        str: The one-time use token to activate the account.
    """
    serializer = URLSafeTimedSerializer(application_secret_key)
    return serializer.dumps(email, salt=application_password_salt)


def confirm_activation_token(
    application_secret_key, application_password_salt, token, expiration=3600
):
    """Allow to validate a pre-generated activation token.

    Args:
        application_secret_key (str): The secret key of the application.
        application_password_salt (str): secret key specific for managing the activation token.
        token (str): The one-time use token to activate the account.
        expiration (int, optional): the expiration time for the token in minutes. Defaults to 3600.

    Returns:
        str: the email represented for this token.
    """
    serializer = URLSafeTimedSerializer(application_secret_key)
    try:
        email = serializer.loads(
            token,
            salt=application_password_salt,
            max_age=expiration,
        )
        return email
    except Exception:
        raise Exception("It was not possible to read the temporary token !")
