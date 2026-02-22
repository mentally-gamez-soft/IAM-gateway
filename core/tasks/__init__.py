"""Celery application factory and task package.

Usage
-----
Celery is initialised lazily via :func:`init_celery`, which is called from
:func:`core.create_app` immediately after the Flask application is fully
configured.  The module-level ``celery`` instance is intentionally created
without any Flask binding so that tasks imported at module level work without
an active application context; the :class:`ContextTask` base class re-pushes
the context on every task execution.

CLI invocation (from project root)::

    celery -A application.celery worker --loglevel=info
"""

import logging

from celery import Celery

logger = logging.getLogger(__name__)

# Module-level Celery instance ─ configured later by init_celery()
celery: Celery = Celery(__name__)


def init_celery(app) -> Celery:
    """Configure the Celery instance with settings from *app.config*.

    Args:
        app: The Flask application instance.

    Returns:
        Celery: The configured Celery instance.
    """
    celery.conf.update(
        broker_url=app.config.get("CELERY_BROKER_URL"),
        result_backend=app.config.get("CELERY_RESULT_BACKEND"),
        task_serializer=app.config.get("CELERY_TASK_SERIALIZER", "json"),
        accept_content=app.config.get("CELERY_ACCEPT_CONTENT", ["json"]),
        task_track_started=app.config.get("CELERY_TASK_TRACK_STARTED", True),
        task_time_limit=app.config.get("CELERY_TASK_TIME_LIMIT", 300),
        task_always_eager=app.config.get("CELERY_TASK_ALWAYS_EAGER", False),
        task_eager_propagates=app.config.get(
            "CELERY_TASK_EAGER_PROPAGATES", False
        ),
        # Route email tasks to a dedicated queue
        task_routes={
            "core.tasks.email_tasks.*": {"queue": "email"},
        },
        # Dead-letter queue: messages rejected after max_retries land here
        task_queues_max_priority=10,
    )

    # Subclass Celery's base Task so every task execution runs inside the
    # Flask application context.  This gives tasks access to current_app,
    # Flask-Mail, SQLAlchemy, etc.
    class ContextTask(celery.Task):  # type: ignore[valid-type]
        """Execute tasks within the Flask application context."""

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    # Keep a reference to the Flask app for tasks that need it at import time
    celery.flask_app = app  # type: ignore[attr-defined]

    logger.info(
        "Celery initialised: broker=%s always_eager=%s",
        celery.conf.broker_url,
        celery.conf.task_always_eager,
    )
    return celery
