"""Define the validate_env_config function."""

from flask import Config


def validate_env_config(app_config: Config):
    """Validate the environment configuration."""
    required_vars = [
        "APP_NAME",
        "APP_VERSION",
        "APP_ENV",
        "SECRET_KEY",
        "SECURITY_PASSWORD_SALT",
        "MEDIA_DIR",
        "UPLOAD_DIR",
        "MAX_FILE_SIZE",
        "APP_ENV_LOCAL",
        "APP_ENV_TESTING",
        "APP_ENV_DEVELOPMENT",
        "APP_ENV_STAGING",
        "APP_ENV_PRODUCTION",
        "LOG_PATH",
        "LOG_FILENAME",
    ]

    if app_config.get("APP_USES_DATABASE", False):
        required_vars.extend(
            [
                "DB_HOSTNAME",
                "DB_PORT",
                "DB_NAME",
                "SQLALCHEMY_DATABASE_URI",
                "SQLALCHEMY_DATABASE_SCHEMA",
            ]
        )
    else:
        print(
            "No database will be used for application, skipping database"
            " configuration validation."
        )

    if app_config.get("APP_SEND_EMAILS", False):
        required_vars.extend(
            [
                "MAIL_SERVER",
                "MAIL_PORT",
                "MAIL_USERNAME",
                "MAIL_PASSWORD",
                "DONT_REPLY_FROM_EMAIL",
                "ADMINS",
            ]
        )
    else:
        print(
            "No emails will be used for application, skipping mail server"
            " configuration validation."
        )

    gw_required_vars = [
        "ENCODING",
        "JWT_ALG",
        "JWT_EXPIRATION_TIME",
        "JWT_ENCODING_PARAM_1",
        "JWT_ENCODING_PARAM_2",
        "JWT_ENCODING_PARAM_3",
    ]

    resilience_required_vars = [
        "CIRCUIT_BREAKER_MAX_FAIL",
        "CIRCUIT_BREAKER_RESET_TIMEOUT",
        "RETRY_CALLS",
    ]

    rate_limit_required_vars = [
        "RATELIMIT_STORAGE_URI",
        "RATE_LIMIT_LOGIN",
        "RATE_LIMIT_SIGNUP",
    ]

    password_reset_required_vars = [
        "PASSWORD_RESET_SALT",
    ]

    required_vars.extend(gw_required_vars)
    required_vars.extend(resilience_required_vars)
    required_vars.extend(rate_limit_required_vars)
    required_vars.extend(password_reset_required_vars)

    print(required_vars)
    print(
        "============================================================================================================"
    )
    print(app_config)

    missing_vars = [var for var in required_vars if not app_config.get(var)]

    if missing_vars:
        raise EnvironmentError(
            "Missing required environment variables:"
            f" {', '.join(missing_vars)}"
        )

    print("Environment config check has passed.")
