"""Load the configuration for local environment.

Raises:
    Exception: Raise an error if the .env file for local environment does not exist.
"""

from dotenv import load_dotenv

from .default import *

if not load_dotenv(join(ENV_DIR, ".env.local")):
    raise Exception("Failed to load .env.local file !!!")

DB_HOSTNAME = env.get("DB_HOSTNAME")
DB_PORT = env.get("DB_PORT")
DB_NAME = env.get("DB_NAME")
SQLALCHEMY_DATABASE_URI = env.get("SQLALCHEMY_DATABASE_URI")
SQLALCHEMY_DATABASE_SCHEMA = env.get("SQLALCHEMY_DATABASE_SCHEMA")
APP_ENV = APP_ENV_LOCAL
DEBUG = True
LOCAL_DEV = True

# Connection pool — reduced footprint for local development
SQLALCHEMY_POOL_SIZE = int(env.get("SQLALCHEMY_POOL_SIZE", 3))
SQLALCHEMY_MAX_OVERFLOW = int(env.get("SQLALCHEMY_MAX_OVERFLOW", 5))
LOG_FORMAT = "text"

# CORS — allow all origins locally for convenience
CORS_ORIGINS = "*"

# Rate limiting - very permissive for local dev
RATE_LIMIT_LOGIN = "100/minute"
RATE_LIMIT_SIGNUP = "100/minute"
RATELIMIT_STORAGE_URI = env.get("RATELIMIT_STORAGE_URI", "memory://")
