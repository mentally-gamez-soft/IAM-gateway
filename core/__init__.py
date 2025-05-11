"""Declare the module of the application."""

from flask import Flask
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from core.users import users_bp
from server.config.logs import configure_logging
from server.config.mails import mail

login_manager = LoginManager()
db = SQLAlchemy()
migrate = Migrate()


def register_blueprints(app):
    """Register all the blue prints of the entry points.

    Args:
        app (_type_): the flask app.

    Returns:
        app: the flask app.
    """
    # Registro de los Blueprints

    app.register_blueprint(users_bp)


def create_app(settings_module="config.DevelopmentConfig"):
    """Create the application loading the config.

    Returns:
        app: the flask application.
    """
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(settings_module)
    # Load the configuration from the instance folder
    # if app.config.get("TESTING", False):
    #     # app.config.from_pyfile("config-testing.py", silent=True)
    #     app.config.from_pyfile("config/testing.py", silent=True)
    # else:
    #     app.config.from_pyfile("config/local.py", silent=True)

    configure_logging(app)

    login_manager.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    register_blueprints(app)

    # Custom error handlers
    register_error_handlers(app)

    return app


def register_error_handlers(app):
    """Add custom error handlers to the app."""

    @app.errorhandler(500)
    def base_error_handler(e):
        return {"message": "Server Error 500 !!!"}, 500

    @app.errorhandler(404)
    def error_404_handler(e):
        return {"message": "Not found Error 404 !!!"}, 404

    @app.errorhandler(401)
    def error_401_handler(e):
        return {"message": "Not Allowed Error 401 !!!"}, 401
