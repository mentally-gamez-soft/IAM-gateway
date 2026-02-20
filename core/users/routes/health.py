"""Define the health check and readiness probe endpoints.

These endpoints are used by container orchestrators (e.g., Docker, Kubernetes)
and load balancers to determine whether the application is alive (liveness) or
ready to serve traffic (readiness). They bypass authentication and CSRF protection.

Endpoints:
    GET /health  — liveness probe (process alive check)
    GET /ready   — readiness probe (database + external services check)
"""

import logging
import smtplib
import socket
from datetime import datetime, timezone

import requests
from flask import current_app, jsonify
from sqlalchemy import text

from core import csrf, db
from core.users import users_bp

logger = logging.getLogger(__name__)

# Individual timeout for each dependency check (seconds)
DEPENDENCY_CHECK_TIMEOUT: int = 3


@users_bp.route("/health", methods=["GET"])
@csrf.exempt
def health():
    """Liveness probe — returns 200 if the application process is running.

    This endpoint performs no external dependency checks. It is intended for
    use by container orchestrators to determine if the application process is
    alive and should be restarted if it fails.

    Returns:
        JSON: {"status": "ok", "timestamp": "<ISO 8601>", "version": "<APP_VERSION>"}
        HTTP 200
    """
    logger.debug("Health liveness probe called.")
    return (
        jsonify(
            {
                "status": "ok",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": current_app.config.get("APP_VERSION", "unknown"),
            }
        ),
        200,
    )


@users_bp.route("/ready", methods=["GET"])
@csrf.exempt
def ready():
    """Readiness probe — returns 200 if all critical dependencies are reachable.

    Performs the following checks:
    - **database**: executes ``SELECT 1`` via SQLAlchemy with a 3-second timeout.
    - **password_api**: sends an HTTP HEAD request to the configured external
      password-scoring API with a 3-second timeout.
    - **smtp**: attempts a TCP connection to the configured SMTP server if
      ``APP_SEND_EMAILS`` is enabled; skipped otherwise.

    Returns:
        JSON: {"status": "ready"|"not_ready", "checks": {...}}
        HTTP 200 if all critical checks pass, HTTP 503 otherwise.
    """
    logger.debug("Health readiness probe called.")

    checks: dict = {}
    all_ok: bool = True

    # ── 1. Database check ──────────────────────────────────────────────────
    checks["database"] = _check_database()
    if checks["database"]["status"] != "ok":
        all_ok = False

    # ── 2. External password-scoring API check ─────────────────────────────
    checks["password_api"] = _check_password_api()
    # Password API is treated as non-critical (warn but don't fail readiness)
    # to avoid cascading failures when the external service is temporarily down.

    # ── 3. SMTP server check (only when email sending is enabled) ──────────
    checks["smtp"] = _check_smtp()
    # SMTP is treated as non-critical for the same reason.

    status = "ready" if all_ok else "not_ready"
    http_code = 200 if all_ok else 503

    logger.info(
        "Readiness probe completed.",
        extra={"status": status, "checks": checks},
    )

    return jsonify({"status": status, "checks": checks}), http_code


# ── Private helpers ────────────────────────────────────────────────────────────


def _collect_pool_metrics() -> dict:
    """Collect SQLAlchemy connection-pool statistics.

    Returns a dict with numeric counters when the underlying pool supports
    them (QueuePool / AsyncAdaptedQueuePool).  For poolless backends (SQLite
    NullPool / StaticPool) returns ``{"available": false}``.

    Adds a ``saturated`` flag and a ``utilization_pct`` float so operators
    can quickly spot pools that are running close to their limit (>80 %
    utilisation triggers ``saturated: true``).

    Returns:
        dict: pool metrics or ``{"available": false}`` if unsupported.
    """
    try:
        pool = db.engine.pool
        pool_size: int = pool.size()
        checked_in: int = pool.checkedin()
        checked_out: int = pool.checkedout()
        overflow: int = pool.overflow()
        # _max_overflow is a private attribute; fall back gracefully
        max_overflow: int = getattr(pool, "_max_overflow", 0)
        capacity: int = pool_size + max_overflow
        utilization_pct: float = (
            round(checked_out / capacity * 100, 1) if capacity > 0 else 0.0
        )
        return {
            "available": True,
            "pool_size": pool_size,
            "checked_out": checked_out,
            "checked_in": checked_in,
            "overflow": overflow,
            "max_overflow": max_overflow,
            "utilization_pct": utilization_pct,
            "saturated": utilization_pct > 80.0,
        }
    except AttributeError:
        # NullPool / StaticPool (SQLite) do not expose size()/checkedin() etc.
        return {"available": False}
    except Exception as exc:  # noqa: BLE001
        logger.debug("Pool metrics collection failed: %s", exc)
        return {"available": False, "detail": str(exc)}


def _check_database() -> dict:
    """Execute ``SELECT 1`` to verify database connectivity.

    Returns:
        dict: {"status": "ok"|"error", "detail": "<message>", "pool": {...}}
    """
    try:
        db.session.execute(text("SELECT 1"))
        return {"status": "ok", "pool": _collect_pool_metrics()}
    except Exception as exc:  # noqa: BLE001
        logger.warning("Database readiness check failed: %s", exc)
        return {"status": "error", "detail": str(exc)}


def _check_password_api() -> dict:
    """Send an HTTP HEAD request to the password-scoring API.

    Returns:
        dict: {"status": "ok"|"error"|"skipped", "detail": "<message>"}
    """
    api_url: str = current_app.config.get("WS_SCORING_PASSWORD_URL_API", "")
    if not api_url:
        return {
            "status": "skipped",
            "detail": "WS_SCORING_PASSWORD_URL_API not configured",
        }

    try:
        response = requests.head(
            api_url, timeout=DEPENDENCY_CHECK_TIMEOUT, allow_redirects=True
        )
        if response.status_code < 500:
            return {"status": "ok"}
        return {
            "status": "error",
            "detail": f"Unexpected HTTP {response.status_code}",
        }
    except requests.exceptions.Timeout:
        logger.warning(
            "Password API readiness check timed out (url=%s).", api_url
        )
        return {"status": "error", "detail": "Connection timed out"}
    except requests.exceptions.ConnectionError as exc:
        logger.warning("Password API readiness check failed: %s", exc)
        return {"status": "error", "detail": str(exc)}
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "Password API readiness check raised an unexpected error: %s", exc
        )
        return {"status": "error", "detail": str(exc)}


def _check_smtp() -> dict:
    """Attempt a TCP connection to the configured SMTP server.

    Returns:
        dict: {"status": "ok"|"error"|"skipped", "detail": "<message>"}
    """
    send_emails: bool = current_app.config.get("APP_SEND_EMAILS", False)
    if not send_emails:
        return {"status": "skipped", "detail": "APP_SEND_EMAILS is disabled"}

    smtp_host: str = current_app.config.get("EMAIL_SERVER", "")
    smtp_port_raw = current_app.config.get("EMAIL_PORT", 587)
    try:
        smtp_port = int(smtp_port_raw)
    except (TypeError, ValueError):
        smtp_port = 587

    if not smtp_host:
        return {"status": "skipped", "detail": "EMAIL_SERVER not configured"}

    try:
        with smtplib.SMTP(
            smtp_host, smtp_port, timeout=DEPENDENCY_CHECK_TIMEOUT
        ):
            pass
        return {"status": "ok"}
    except socket.timeout:
        logger.warning(
            "SMTP readiness check timed out (%s:%s).", smtp_host, smtp_port
        )
        return {"status": "error", "detail": "Connection timed out"}
    except (smtplib.SMTPException, OSError) as exc:
        logger.warning("SMTP readiness check failed: %s", exc)
        return {"status": "error", "detail": str(exc)}
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "SMTP readiness check raised an unexpected error: %s", exc
        )
        return {"status": "error", "detail": str(exc)}
