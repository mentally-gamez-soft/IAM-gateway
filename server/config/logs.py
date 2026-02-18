"""Define the configuration for the logs server.

Supports two log formats controlled by the LOG_FORMAT config variable:
- "text": Human-readable format for local/dev/testing environments
- "json": Structured JSON format for staging/production environments

The JSON formatter produces log entries compatible with log aggregation
tools such as ELK, Loki, and Datadog. Each JSON log entry includes:
timestamp, level, logger, function, lineno, request_id, user_id,
remote_addr, method, path, environment, and message.
"""

import logging
import uuid
from datetime import datetime, timezone
from logging.handlers import SMTPHandler
from os.path import join

from pythonjsonlogger import jsonlogger


class RequestContextFilter(logging.Filter):
    """Logging filter that enriches log records with request-scoped context.

    Injects request_id, user_id, remote_addr, method, and path into every
    log record when inside a Flask request context. Gracefully omits these
    fields when logging occurs outside of a request context (e.g., at
    application startup or in background tasks).
    """

    def filter(self, record):
        """Enrich the log record with request context fields.

        Args:
            record (logging.LogRecord): The log record to enrich.

        Returns:
            bool: Always True so the record is not filtered out.
        """
        try:
            from flask import g, request

            # Inject or generate request_id
            request_id = getattr(g, "request_id", None)
            if not request_id:
                request_id = str(uuid.uuid4())
                g.request_id = request_id
            record.request_id = request_id

            # Inject user_id from Flask-Login current_user
            try:
                from flask_login import current_user

                if current_user and current_user.is_authenticated:
                    record.user_id = str(current_user.id)
                else:
                    record.user_id = None
            except Exception:
                record.user_id = None

            record.remote_addr = request.remote_addr
            record.method = request.method
            record.path = request.path

        except RuntimeError:
            # Outside of Flask request context (startup, background tasks)
            record.request_id = None
            record.user_id = None
            record.remote_addr = None
            record.method = None
            record.path = None

        return True


class JsonLogFormatter(jsonlogger.JsonFormatter):
    """Custom JSON log formatter producing structured log entries.

    Extends pythonjsonlogger.JsonFormatter to add required IAM-Gateway
    fields: timestamp (ISO 8601), level, logger, function, lineno,
    request_id, user_id, remote_addr, method, path, environment,
    and message.
    """

    def __init__(self, app_env="unknown", *args, **kwargs):
        """Initialise the formatter with the current application environment.

        Args:
            app_env (str): The current application environment name.
        """
        super().__init__(*args, **kwargs)
        self.app_env = app_env

    def add_fields(self, log_record, record, message_dict):
        """Override to inject structured fields into every JSON log entry.

        Args:
            log_record (dict): The dict being built for JSON output.
            record (logging.LogRecord): The original log record.
            message_dict (dict): Extra fields from the log call.
        """
        super().add_fields(log_record, record, message_dict)

        # Timestamp in ISO 8601 format with UTC timezone
        log_record["timestamp"] = datetime.now(tz=timezone.utc).isoformat()

        # Core log fields
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["function"] = record.funcName
        log_record["lineno"] = record.lineno
        log_record["environment"] = self.app_env

        # Request context fields (set by RequestContextFilter)
        log_record["request_id"] = getattr(record, "request_id", None)
        log_record["user_id"] = getattr(record, "user_id", None)
        log_record["remote_addr"] = getattr(record, "remote_addr", None)
        log_record["method"] = getattr(record, "method", None)
        log_record["path"] = getattr(record, "path", None)


def set_logging_mail_handler(app, log_level) -> dict:
    """Configure the application with the email credentials if the app is ready for it.

    Args:
        app (Flask): the flask app
        log_level (str): The log level to set.

    Returns:
        dict: contains the status True if the email logging is set and the handler.
    """
    result = {"status": False, "handler": None}

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
        log_format = app.config.get("LOG_FORMAT", "text")
        if log_format == "json":
            mail_handler.setFormatter(
                JsonLogFormatter(app_env=app.config.get("APP_ENV", "unknown"))
            )
        else:
            mail_handler.setFormatter(mail_handler_formatter())
        result["status"] = True
        result["handler"] = mail_handler
    return result


def logging_formatter():
    """Define the logger formatter for the console (human-readable text)."""
    return logging.Formatter(
        "[%(asctime)s.%(msecs)d]\t %(levelname)s"
        " \t[%(name)s.%(funcName)s:%(lineno)d]\t %(message)s",
        datefmt="%d/%m/%Y %H:%M:%S",
    )


def mail_handler_formatter():
    """Define the logger formatter for the emails (human-readable text)."""
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
    """Configure the loggers for the application.

    Selects between JSON (structured) and text (human-readable) log
    formats based on the LOG_FORMAT configuration variable:
    - LOG_FORMAT="json":  staging and production environments
    - LOG_FORMAT="text":  local, testing, and development environments

    A RequestContextFilter is attached to all handlers to enrich log
    records with request_id, user_id, and request metadata when inside
    a Flask request context.
    """
    LOG_LEVEL_DEBUG = logging.DEBUG
    LOG_LEVEL_INFO = logging.INFO
    LOG_LEVEL_ERROR = logging.ERROR  # noqa: F841

    log_format = app.config.get("LOG_FORMAT", "text")
    app_env = app.config.get("APP_ENV", "unknown")

    # Determine the appropriate formatter based on LOG_FORMAT config
    if log_format == "json":
        active_formatter = JsonLogFormatter(app_env=app_env)
    else:
        active_formatter = logging_formatter()

    # Request context filter enriches every record with request metadata
    context_filter = RequestContextFilter()

    # Close and remove any existing handlers to avoid resource leaks.
    for _handler in app.logger.handlers[:]:
        _handler.close()
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
    console_handler.setFormatter(active_formatter)
    console_handler.addFilter(context_filter)

    # -------------------------------------------------------------------
    # Creation of a filelog handler
    # -------------------------------------------------------------------
    file_handler = logging.FileHandler(
        filename=join(
            app.config.get("LOG_PATH"), app.config.get("LOG_FILENAME")
        ),
    )
    file_handler.setFormatter(active_formatter)
    file_handler.addFilter(context_filter)

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
            mail_log["handler"].addFilter(context_filter)
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
