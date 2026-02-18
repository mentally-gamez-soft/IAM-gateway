"""Declare the routes module."""

import logging
import uuid

from core import login_manager
from core.users.models import GwUser

from . import (
    email_activation,
    login,
    logout,
    password_reset,
    roles,
    sanity_check,
    signup,
)

logger = logging.getLogger(__name__)


@login_manager.user_loader
def load_user(user_id: uuid):
    """Load the user session.

    Args:
        user_id (uuid): The id of the user.

    Returns:
        user: an instance for the logged in user.
    """
    logger.info("Try to reload the user from session.")
    return GwUser.get_by_id(user_id)
