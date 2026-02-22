import importlib
import logging
import os
import sys
from logging.config import fileConfig
from urllib.parse import urlparse

from alembic import context
from sqlalchemy import text

# ---------------------------------------------------------------------------
# Alembic config object — provides access to values in alembic.ini
# ---------------------------------------------------------------------------
config = context.config

# Set up loggers from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
logger = logging.getLogger("alembic.env")

# Ensure the project root is importable (needed for standalone alembic runs)
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mask_db_url(url: str) -> str:
    """Return the DB URL with the password replaced by ***."""
    parsed = urlparse(url)
    if parsed.password:
        return url.replace(parsed.password, "***")
    return url


def _get_url_from_settings_module() -> str:
    """Load SQLALCHEMY_DATABASE_URI from the APP_SETTINGS_MODULE config module.

    Raises:
        RuntimeError: when APP_SETTINGS_MODULE is not set or the module does
            not expose SQLALCHEMY_DATABASE_URI.
    """
    settings_module = os.environ.get("APP_SETTINGS_MODULE")
    if not settings_module:
        raise RuntimeError(
            "No Flask application context is available and the "
            "APP_SETTINGS_MODULE environment variable is not set.\n"
            "Set APP_SETTINGS_MODULE to one of: "
            "config.local | config.dev | config.staging | config.prod"
        )

    try:
        module = importlib.import_module(settings_module)
    except ImportError as exc:
        raise RuntimeError(
            f"Failed to import configuration module '{settings_module}': {exc}"
        ) from exc

    db_url = getattr(module, "SQLALCHEMY_DATABASE_URI", None)
    if not db_url:
        raise RuntimeError(
            f"SQLALCHEMY_DATABASE_URI is not defined (or is empty) in "
            f"'{settings_module}'. "
            "Ensure the required environment variables are loaded for that "
            "environment (e.g. via the corresponding .env file)."
        )

    logger.info(
        "Migration target from '%s': %s", settings_module, _mask_db_url(db_url)
    )
    return db_url


def _get_schema() -> str | None:
    """Return SQLALCHEMY_DATABASE_SCHEMA for the target environment, or None.

    Resolution order mirrors get_database_url():
    1. Flask application context (normal ``flask db`` usage)
    2. APP_SETTINGS_MODULE environment variable (standalone Alembic / CI)

    Returns None when:
    - The config key is absent, empty, or the literal string "None"
    - No settings module can be found
    """
    # 1. Flask context
    try:
        from flask import current_app  # noqa: PLC0415

        schema = current_app.config.get("SQLALCHEMY_DATABASE_SCHEMA")
        if schema and schema.lower() not in ("none", "public", ""):
            return schema
        return None
    except RuntimeError:
        pass

    # 2. APP_SETTINGS_MODULE fallback
    settings_module = os.environ.get("APP_SETTINGS_MODULE")
    if settings_module:
        try:
            module = importlib.import_module(settings_module)
            schema = getattr(module, "SQLALCHEMY_DATABASE_SCHEMA", None)
            if schema and str(schema).lower() not in ("none", "public", ""):
                logger.info(
                    "Migration schema from '%s': %s", settings_module, schema
                )
                return str(schema)
        except ImportError:
            pass

    return None


def _try_flask_context():
    """Return (engine, url, db, migrate_conf_args) from Flask context.

    Returns a tuple of four Nones when no application context is active.
    """
    try:
        from flask import current_app  # noqa: PLC0415

        db = current_app.extensions["migrate"].db
        try:
            engine = db.get_engine()
        except (TypeError, AttributeError):
            engine = db.engine

        try:
            url = engine.url.render_as_string(hide_password=False).replace(
                "%", "%%"
            )
        except AttributeError:
            url = str(engine.url).replace("%", "%%")

        conf_args = current_app.extensions["migrate"].configure_args
        logger.info(
            "Migration target from Flask context: %s", _mask_db_url(url)
        )
        return engine, url, db, conf_args

    except RuntimeError:
        # No active Flask application context
        return None, None, None, None


def get_database_url() -> str:
    """Return the database URL for migrations.

    Resolution order:
    1. Flask application context / Flask-Migrate  (normal ``flask db`` usage)
    2. APP_SETTINGS_MODULE environment variable   (standalone Alembic / CI)
    """
    _, url, _, _ = _try_flask_context()
    if url:
        return url
    return _get_url_from_settings_module()


def _get_metadata():
    """Return the SQLAlchemy metadata object for autogenerate support."""
    _, _, db, _ = _try_flask_context()
    if db is not None:
        if hasattr(db, "metadatas"):
            return db.metadatas[None]
        return db.metadata

    # No Flask context — import db + models directly so the metadata is
    # populated before Alembic inspects it.
    import core.users.models  # noqa: F401, PLC0415
    from core import db as core_db  # noqa: PLC0415

    return core_db.metadata


def _process_revision_directives(context, revision, directives):
    """Skip empty auto-generated migrations.

    Reference: http://alembic.zzzcomputing.com/en/latest/cookbook.html
    """
    if getattr(config.cmd_opts, "autogenerate", False):
        script = directives[0]
        if script.upgrade_ops.is_empty():
            directives[:] = []
            logger.info("No changes in schema detected.")


# ---------------------------------------------------------------------------
# Migration runners
# ---------------------------------------------------------------------------


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    Configures the context with just a URL and not an Engine.  Skipping
    Engine creation means no DBAPI connection is required.

    Calls to context.execute() emit the given string to the script output.
    """
    url = get_database_url()
    schema = _get_schema()
    configure_kwargs: dict = dict(
        url=url,
        target_metadata=_get_metadata(),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    if schema:
        configure_kwargs["include_schemas"] = True
        configure_kwargs["version_table_schema"] = schema
        logger.info("Offline migration target schema: %s", schema)
    context.configure(**configure_kwargs)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    Creates an Engine and associates a connection with the context.
    When a Flask application context is active the existing Flask-Migrate
    engine is reused; otherwise a fresh engine is built from the URL
    resolved via APP_SETTINGS_MODULE.
    """
    engine, url, _, conf_args = _try_flask_context()

    if engine is not None:
        # ── Flask context path (normal `flask db` usage) ─────────────────
        if conf_args is None:
            conf_args = {}
        if conf_args.get("process_revision_directives") is None:
            conf_args["process_revision_directives"] = (
                _process_revision_directives
            )

        schema = _get_schema()
        if schema:
            conf_args.setdefault("include_schemas", True)
            conf_args.setdefault("version_table_schema", schema)
            logger.info(
                "Online migration target schema (Flask ctx): %s", schema
            )

        with engine.connect() as connection:
            if schema:
                connection.execute(
                    text(f"SET search_path TO {schema}, public")
                )
            context.configure(
                connection=connection,
                target_metadata=_get_metadata(),
                **conf_args,
            )
            with context.begin_transaction():
                context.run_migrations()
    else:
        # ── Standalone / CI path (APP_SETTINGS_MODULE) ────────────────────
        from sqlalchemy import engine_from_config, pool  # noqa: PLC0415

        db_url = _get_url_from_settings_module()
        connectable = engine_from_config(
            {"sqlalchemy.url": db_url},
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        schema = _get_schema()
        with connectable.connect() as connection:
            if schema:
                connection.execute(
                    text(f"SET search_path TO {schema}, public")
                )
                logger.info(
                    "Online migration target schema (standalone): %s", schema
                )
            configure_kwargs: dict = dict(
                connection=connection,
                target_metadata=_get_metadata(),
                process_revision_directives=_process_revision_directives,
            )
            if schema:
                configure_kwargs["include_schemas"] = True
                configure_kwargs["version_table_schema"] = schema
            context.configure(**configure_kwargs)
            with context.begin_transaction():
                context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
