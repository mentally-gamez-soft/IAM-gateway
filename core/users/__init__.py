"""Declare the blueprints for the module for user management."""

from flask import Blueprint

users_bp = Blueprint("users", __name__, url_prefix="/api/v1")
health_bp = Blueprint("health", __name__)

from core.users import routes
