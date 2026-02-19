"""Legacy unversioned routes with HTTP deprecation headers (US-006).

These routes maintain backward compatibility for API consumers still using
pre-v1 unversioned endpoints. Each legacy route proxies the request to the
corresponding versioned handler under ``/api/v1/`` and adds the following
HTTP headers to the response:

  - ``Deprecation: true``
  - ``Sunset: <SUNSET_DATE>`` — planned removal date (6 months from release)
  - ``Link: </api/v1/...>; rel="successor-version"`` — canonical resource URL

Clients are strongly encouraged to migrate before the sunset date.
This blueprint can be removed cleanly by unregistering it from
``core/__init__.py:register_blueprints``.
"""

import logging

from flask import Blueprint, after_this_request

logger = logging.getLogger(__name__)

legacy_bp = Blueprint("legacy", __name__)

# ── Deprecation configuration ─────────────────────────────────────────────────
SUNSET_DATE: str = "2026-09-01"


def _add_deprecation_headers(versioned_path: str) -> None:
    """Register an ``after_this_request`` hook to inject deprecation headers.

    This function must be called at the start of each legacy view function.
    The header injection happens after the wrapped view function returns its
    response, ensuring the headers are always present.

    Args:
        versioned_path: The canonical versioned path (e.g. ``/api/v1/login``).
    """

    @after_this_request
    def _inject(response):
        response.headers["Deprecation"] = "true"
        response.headers["Sunset"] = SUNSET_DATE
        response.headers["Link"] = '<{}>; rel="successor-version"'.format(
            versioned_path
        )
        return response


# ── Legacy route handlers ─────────────────────────────────────────────────────


@legacy_bp.route("/signup", methods=("POST",))
def legacy_signup():
    """Forward POST /signup to the versioned /api/v1/signup endpoint."""
    logger.warning(
        "Deprecated route /signup accessed. Migrate to /api/v1/signup."
    )
    _add_deprecation_headers("/api/v1/signup")
    from core.users.routes.signup import signup

    return signup()


@legacy_bp.route("/login", methods=["POST"])
def legacy_login():
    """Forward POST /login to the versioned /api/v1/login endpoint."""
    logger.warning(
        "Deprecated route /login accessed. Migrate to /api/v1/login."
    )
    _add_deprecation_headers("/api/v1/login")
    from core.users.routes.login import login

    return login()


@legacy_bp.route("/logout", methods=["POST"])
def legacy_logout():
    """Forward POST /logout to the versioned /api/v1/logout endpoint."""
    logger.warning(
        "Deprecated route /logout accessed. Migrate to /api/v1/logout."
    )
    _add_deprecation_headers("/api/v1/logout")
    from core.users.routes.logout import logout

    return logout()


@legacy_bp.route("/confirm/<token>", methods=["GET"])
def legacy_confirm_email(token):
    """Forward GET /confirm/<token> to the versioned /api/v1/confirm/<token> endpoint."""
    logger.warning(
        "Deprecated route /confirm/<token> accessed. "
        "Migrate to /api/v1/confirm/<token>."
    )
    _add_deprecation_headers("/api/v1/confirm/{}".format(token))
    from core.users.routes.email_activation import confirm_email

    return confirm_email(token)


@legacy_bp.route("/resend-confirmation", methods=["GET"])
def legacy_resend_confirmation():
    """Forward GET /resend-confirmation to the versioned /api/v1/resend-confirmation."""
    logger.warning(
        "Deprecated route /resend-confirmation accessed. "
        "Migrate to /api/v1/resend-confirmation."
    )
    _add_deprecation_headers("/api/v1/resend-confirmation")
    from core.users.routes.email_activation import resend_confirmation_email

    return resend_confirmation_email()


@legacy_bp.route("/role/add", methods=["POST"])
def legacy_add_role():
    """Forward POST /role/add to the versioned /api/v1/role/add endpoint."""
    logger.warning(
        "Deprecated route /role/add accessed. Migrate to /api/v1/role/add."
    )
    _add_deprecation_headers("/api/v1/role/add")
    from core.users.routes.roles import add_role

    return add_role()


@legacy_bp.route("/forgot-password", methods=["POST"])
def legacy_forgot_password():
    """Forward POST /forgot-password to the versioned /api/v1/forgot-password endpoint."""
    logger.warning(
        "Deprecated route /forgot-password accessed. "
        "Migrate to /api/v1/forgot-password."
    )
    _add_deprecation_headers("/api/v1/forgot-password")
    from core.users.routes.password_reset import forgot_password

    return forgot_password()


@legacy_bp.route("/reset-password/<token>", methods=["POST"])
def legacy_reset_password(token):
    """Forward POST /reset-password/<token> to the versioned /api/v1/reset-password/<token> endpoint."""
    logger.warning(
        "Deprecated route /reset-password/<token> accessed. "
        "Migrate to /api/v1/reset-password/<token>."
    )
    _add_deprecation_headers("/api/v1/reset-password/{}".format(token))
    from core.users.routes.password_reset import reset_password

    return reset_password(token)


@legacy_bp.route("/token/refresh", methods=["POST"])
def legacy_token_refresh():
    """Forward POST /token/refresh to the versioned /api/v1/token/refresh endpoint."""
    logger.warning(
        "Deprecated route /token/refresh accessed. "
        "Migrate to /api/v1/token/refresh."
    )
    _add_deprecation_headers("/api/v1/token/refresh")
    from core.users.routes.token import refresh_token

    return refresh_token()
