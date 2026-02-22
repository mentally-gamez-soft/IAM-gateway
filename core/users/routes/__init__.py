"""Declare the routes module."""

import logging
import uuid

from core import login_manager
from core.users.models import GwUser

from . import (
    email_activation,
    gdpr,
    health,
    login,
    logout,
    password_reset,
    roles,
    sanity_check,
    signup,
    token,
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
    if user_id is None:
        return None  # ← guard prevents loop on anonymous requests
    user = GwUser.get_by_id(user_id)
    if user is None or user.deleted:
        return None
    return user
