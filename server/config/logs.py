"""Define the configuration for the logs server."""

import logging
from logging.handlers import SMTPHandler


def verbose_formatter():
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
    # Delete all falut logger handlers if any existing.
    del app.logger.handlers[:]

    # Add our default logger to the list of loggers.
    loggers = [
        app.logger,
    ]
    handlers = []

    # Create a handler to write through the console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(verbose_formatter())

    if app.config["APP_ENV"] in (
        app.config["APP_ENV_LOCAL"],
        app.config["APP_ENV_TESTING"],
        app.config["APP_ENV_DEVELOPMENT"],
    ):
        console_handler.setLevel(logging.DEBUG)
        handlers.append(console_handler)

    elif app.config["APP_ENV"] == app.config["APP_ENV_PRODUCTION"]:
        console_handler.setLevel(logging.INFO)
        handlers.append(console_handler)

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
        mail_handler.setLevel(logging.ERROR)
        mail_handler.setFormatter(mail_handler_formatter())
        handlers.append(mail_handler)

    # Bind each handlers to each loggers
    for logger in loggers:
        for handler in handlers:
            logger.addHandler(handler)
        logger.propagate = False
        logger.setLevel(logging.DEBUG)
