"""Declare the blueprints for the module for user management."""

from flask import Blueprint

users_bp = Blueprint("users", __name__)

from core.users import routes
