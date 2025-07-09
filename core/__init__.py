"""Declare the module of the application."""

from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

from config.validate_config import validate_env_config
from core.swagger.swagger_config import SWAGGER_URL, swaggerui_blueprint
from core.users import users_bp
from server.config.logs import configure_logging
from server.config.mails import mail

csrf = CSRFProtect()
login_manager = LoginManager()
db = SQLAlchemy()


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

    app.register_blueprint(users_bp)
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

    configure_logging(app)

    login_manager.init_app(app)
    set_session_schema(schema=app.get("SQLALCHEMY_DATABASE_SCHEMA"))
    csrf.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    validate_env_config(app.config)
    register_blueprints(app)

    register_error_handlers(app)

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
