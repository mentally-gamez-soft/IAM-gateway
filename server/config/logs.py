"""Define the configuration for the logs server."""

import logging
from logging.handlers import SMTPHandler
from os.path import join


def set_logging_mail_handler(app, log_level) -> dict:
    """Configure the application with the email credentials if the app is ready for it.

    Args:
        app (Flask): the flask app
        log_level (str): The log level to set.

    Returns:
        dict: contains the status True if the email looging is set and the handler.
    """
    result = {"status": False}
    result = {"handler": None}

    if app.config["APP_SEND_EMAILS"]:
        mail_handler = SMTPHandler(
            (app.config["MAIL_SERVER"], app.config["MAIL_PORT"]),
            app.config["DONT_REPLY_FROM_EMAIL"],
            app.config["ADMINS"],
            "[Error][{}] - An undefined error occured".format(
                app.config["APP_ENV"]
            ),
            (app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"]),
            (),
        )

        mail_handler.setLevel(log_level)
        mail_handler.setFormatter(mail_handler_formatter())
        result["status"] = True
        result["handler"] = mail_handler
    return result


def logging_formatter():
    """Define the logger formatter for the console."""
    return logging.Formatter(
        "[%(asctime)s.%(msecs)d]\t %(levelname)s"
        " \t[%(name)s.%(funcName)s:%(lineno)d]\t %(message)s",
        datefmt="%d/%m/%Y %H:%M:%S",
    )


def mail_handler_formatter():
    """Define the logger formatter for the emails."""
    return logging.Formatter(
        """
            Message type:       %(levelname)s
            Location:           %(pathname)s:%(lineno)d
            Module:             %(module)s
            Function:           %(funcName)s
            Time:               %(asctime)s.%(msecs)d

            Message:

            %(message)s
        """,
        datefmt="%d/%m/%Y %H:%M:%S",
    )


def configure_logging(app):
    """Configure the loggers for the application."""
    LOG_LEVEL_DEBUG = logging.DEBUG
    LOG_LEVEL_INFO = logging.INFO
    LOG_LEVEL_ERROR = logging.ERROR

    # Delete all falut logger handlers if any existing.
    del app.logger.handlers[:]

    # Add our default logger to the list of loggers.
    loggers = [
        app.logger,
    ]
    handlers = []

    # -------------------------------------------------------------------
    # Creation of a logs handler for the console / std output
    # -------------------------------------------------------------------
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging_formatter())

    # -------------------------------------------------------------------
    # Creation of a filelog handler
    # -------------------------------------------------------------------
    file_handler = logging.FileHandler(
        filename=join(
            app.config.get("LOG_PATH"), app.config.get("LOG_FILENAME")
        ),
    )
    file_handler.setFormatter(logging_formatter())

    if app.config["APP_ENV"] in (
        app.config["APP_ENV_LOCAL"],
        app.config["APP_ENV_TESTING"],
        app.config["APP_ENV_DEVELOPMENT"],
    ):
        LOG_LEVEL = LOG_LEVEL_DEBUG
    elif app.config["APP_ENV"] in (
        app.config["APP_ENV_PRODUCTION"],
        app.config["APP_ENV_STAGING"],
    ):
        LOG_LEVEL = LOG_LEVEL_INFO

        mail_log = set_logging_mail_handler(app, LOG_LEVEL)
        if mail_log["status"]:
            handlers.append(mail_log["handler"])

    console_handler.setLevel(LOG_LEVEL)
    file_handler.setLevel(LOG_LEVEL)
    handlers.append(console_handler)
    handlers.append(file_handler)

    # Bind each handlers to each loggers
    for logger in loggers:
        for handler in handlers:
            logger.addHandler(handler)
        logger.propagate = False
        logger.setLevel(LOG_LEVEL)
