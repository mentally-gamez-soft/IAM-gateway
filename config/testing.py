"""Load the configuration for testing environment.

Raises:
    Exception: Raise an error if the .env file for testing environment does not exist.
"""

from dotenv import load_dotenv

from .default import *

if not load_dotenv(join(ENV_DIR, ".env.testing")):
    raise Exception("Failed to load .env.testing file !!!")

DB_HOSTNAME = env.get("DB_HOSTNAME")
DB_PORT = env.get("DB_PORT")
DB_NAME = env.get("DB_NAME")
SQLALCHEMY_DATABASE_URI = env.get("SQLALCHEMY_DATABASE_URI")
SQLALCHEMY_DATABASE_SCHEMA = env.get("SQLALCHEMY_DATABASE_SCHEMA")
APP_ENV = APP_ENV_TESTING
DEBUG = True
TESTING = True

# Connection pool — minimal pool for fast, isolated unit tests
SQLALCHEMY_POOL_SIZE = int(env.get("SQLALCHEMY_POOL_SIZE", 2))
SQLALCHEMY_MAX_OVERFLOW = int(env.get("SQLALCHEMY_MAX_OVERFLOW", 3))
WTF_CSRF_ENABLED = False
LOG_FORMAT = "text"

# CORS — allow all origins during automated tests
CORS_ORIGINS = "*"

# Rate limiting - very high thresholds and memory backend for tests
RATE_LIMIT_LOGIN = "1000/minute"
RATE_LIMIT_SIGNUP = "1000/minute"
RATELIMIT_STORAGE_URI = "memory://"
RATELIMIT_HEADERS_ENABLED = True

# Celery — run tasks eagerly (synchronous) during tests, no broker required
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True
USE_ASYNC_EMAIL = False
