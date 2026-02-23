"""Define all the messages of the application."""

__ACCESS_DENIED = "Access denied!"
__AUTH_REQUIRED = "Authorization required."
__ACTIVATION_REQUIRED = "Account activation required."
__ACTIVATION_MSG = "You must activate your account first!"
__LOGIN_MSG = "You must login first!"
__LOGIN_SUCCESSFUL = "You are now logged in."
__LOGOUT_SUCCESSFUL = "You are now logged out."
__ROLE_ADD_SUCCESSFUL = "The new role has been added successfully to user."
__USERNAME_INVALID = "The username is invalid !"
__EMAIL_INVALID = "The email is invalid !"
__USER_CREATION_ERROR = "Error when creating user !"
__USER_WITH_EMAIL_ALREADY_EXISTS = "A user already exists for this email !"
__WELCOME_BACK = "Welcome back !"
__SIGNUP_SUCCESSFUL = "You successfully signed up."
__ACTIVATION_SUCCESSFUL = "Congratulations, your account is now activated."
__INVALID_TOKEN_ERROR = (  # nosec - it is not a hardcoded password.
    "Invalid token !"
)
__DEMAND_RENEW_ACTIVATION = (
    "The confirmation token has expired. Please ask for a new activation"
    " token."
)
__EMAIL_RESENT = "A new confirmation email has been sent."
__GENERIC_ERROR = "Something went wrong."
__ACCOUNT_ACTIVATED = "Your account has been activated."
__ACCOUNT_ALREADY_ACTIVATED = "Your account is already active."
__PAYLOAD_INVALID = "The provided data input is invalid!"
__ACCOUNT_DELETED = "Your account has been deleted."
__ACCOUNT_ALREADY_DELETED = "This account has already been deleted."
__ACCOUNT_DELETE_CONFIRM_REQUIRED = "Deletion confirmation is required."
__ACCOUNT_DELETE_PASSWORD_INVALID = (
    "Incorrect password provided."  # nosec B105
)
__ACCOUNT_DELETE_SUCCESSFUL = "Your account has been successfully deleted."
__DATA_EXPORT_SUCCESSFUL = "Your data has been exported successfully."
__CONSENT_UPDATE_SUCCESSFUL = (
    "Your consent preferences have been updated successfully."
)
__CONSENT_RETRIEVE_SUCCESSFUL = (
    "Your consent preferences have been retrieved successfully."
)
__DELETED_USER_ACCESS_DENIED = "Access denied!"
__PROFILE_GET_SUCCESSFUL = "Profile retrieved successfully."
__PROFILE_UPDATE_SUCCESSFUL = "Profile updated successfully."
__PROFILE_FIELD_PROTECTED = (
    "Protected field(s) cannot be updated via this endpoint."
)
__PROFILE_LANGUAGE_INVALID = "Invalid language_preference value. Expected a 2-5 character locale code (e.g. 'en', 'fr')."
__PROFILE_TIMEZONE_INVALID = (
    "Invalid timezone value. Must be 50 characters or fewer."
)
__PROFILE_DISPLAY_NAME_TOO_LONG = (
    "display_name must be 80 characters or fewer."
)
__PROFILE_AVATAR_URL_TOO_LONG = "avatar_url must be 255 characters or fewer."
