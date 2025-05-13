"""Define all the messages of the application."""

__ACCESS_DENIED = "Access denied!"
__AUTH_REQUIRED = "Authorization required."
__ACTIVATION_REQUIRED = "Account activation required."
__ACTIVATION_MSG = "You must activate your account first!"
__LOGIN_MSG = "You must login first!"
__USERNAME_INVALID = "The username is invalid !"
__EMAIL_INVALID = "The email is invalid !"
__USER_CREATION_ERROR = "Error when creating user !"
__USER_WITH_EMAIL_ALREADY_EXISTS = "A user already exists for this email !"
__WELCOME_BACK = "Welcome back !"
__SIGNUP_SUCCESSFUL = "You successfully signed up."
__ACTIVATION_SUCCESSFUL = "Congratulations, your account is now activated."
__INVALID_TOKEN_ERROR = (  # nosec - it is not hardcoded password.
    "Invalid token !"
)
__DEMAND_RENEW_ACTIVATION = (
    "The confirmation token has expired. Please renew your demand of"
    " activation."
)
__EMAIL_RESENT = "A new confirmation email has been sent."
__GENERIC_ERROR = "Something went wrong."
__ACCOUNT_ACTIVATED = "Your account has been activated."
