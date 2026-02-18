"""Declare the module of the application."""

import uuid

from flask import Flask, g, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

from config.validate_config import validate_env_config
from server.config.logs import configure_logging
from server.config.mails import mail

csrf = CSRFProtect()
login_manager = LoginManager()
db = SQLAlchemy()
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[],
    storage_uri="memory://",
)


def set_session_schema(schema: str):
    """Set the schema database to use.

    Args:
        schema (str): name of the schema DB.
    """
    db.session.connection(
        execution_options={"schema_translate_map": {"per_env": schema}}
    )


def get_session_with_schema():
    """Retrieve the database schema session.

    Returns:
        Session: the current db session object.
    """
    return db.session


migrate = Migrate()


def register_blueprints(app):
    """Register all the blue prints of the entry points.

    Args:
        app (_type_): the flask app.

    Returns:
        app: the flask app.
    """
    # Register the Blueprints
    from core.users import users_bp

    app.register_blueprint(users_bp)

    from core.swagger.swagger_config import SWAGGER_URL, swaggerui_blueprint

    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


def create_app(settings_module="config.dev") -> Flask:
    """Create the application loading the config.

    Returns:
        app: the flask application.
    """
    app = Flask(
        __name__,
        static_url_path="/static",
        static_folder="../static",
        instance_relative_config=True,
    )
    app.config.from_object(settings_module)

    if app.config.get("TESTING", False):
        app.config.from_pyfile("config/testing.py", silent=True)
    elif app.config.get("LOCAL_DEV", False):
        app.config.from_pyfile("config/local.py", silent=True)

    validate_env_config(app.config)

    configure_logging(app)

    @app.before_request
    def inject_request_id():
        """Generate or propagate a unique request ID for every request.

        Reads X-Request-ID from the incoming request header if present,
        otherwise generates a new UUID4. Stored in Flask's g object so
        that the RequestContextFilter can include it in every log record.
        """
        g.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    login_manager.init_app(app)
    print("login manager plugin loaded.")

    # if not app.config.get("LOCAL_DEV", False) and not app.config.get("TESTING", False):
    #     set_session_schema(schema=app.get("SQLALCHEMY_DATABASE_SCHEMA"))

    csrf.init_app(app)
    print("csrf plugin loaded.")

    db.init_app(app)
    print("database plugin loaded.")

    migrate.init_app(app, db)
    print("migrate plugin loaded.")

    mail.init_app(app)
    print("mail plugin loaded.")

    # Reconfigure limiter with the storage URI from app config then init
    limiter._storage_uri = app.config.get("RATELIMIT_STORAGE_URI", "memory://")
    limiter.init_app(app)
    print("rate limiter plugin loaded.")

    register_blueprints(app)
    print("blueprints plugin loaded.")

    register_error_handlers(app)
    print("error handlers loaded.")

    app.json.compact = False

    return app


def register_error_handlers(app):
    """Add custom error handlers to the app."""

    @app.errorhandler(500)
    def base_error_handler(e):
        return {"message": "Internal Server, Error 500 !!!"}, 500

    @app.errorhandler(404)
    def error_404_handler(e):
        return {"message": "Not found, Error 404 !!!"}, 404

    @app.errorhandler(401)
    def error_401_handler(e):
        return {"message": "Not Authenticated, Error 401 !!!"}, 401

    @app.errorhandler(403)
    def error_403_handler(e):
        return {"message": "Not Allowed, Error 403 !!!"}, 401

    @app.errorhandler(429)
    def error_429_handler(e):
        return (
            jsonify(
                {
                    "message": "Too Many Requests. Rate limit exceeded.",
                    "status": 429,
                }
            ),
            429,
        )
