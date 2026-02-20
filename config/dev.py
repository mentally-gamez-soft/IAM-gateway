"""Load the configuration for development environment.

Raises:
    Exception: Raise an error if the .env file for development environment does not exist.
"""

from dotenv import load_dotenv

from .default import *

if not load_dotenv(join(ENV_DIR, ".env.dev")):
    raise Exception("Failed to load .env.dev file !!!")

DB_HOSTNAME = env.get("DB_HOSTNAME")
DB_PORT = env.get("DB_PORT")
DB_NAME = env.get("DB_NAME")
SQLALCHEMY_DATABASE_URI = env.get("SQLALCHEMY_DATABASE_URI")
SQLALCHEMY_DATABASE_SCHEMA = env.get("SQLALCHEMY_DATABASE_SCHEMA")
APP_ENV = APP_ENV_DEVELOPMENT
DEBUG = True

# Connection pool — standard footprint for development environment
SQLALCHEMY_POOL_SIZE = int(env.get("SQLALCHEMY_POOL_SIZE", 5))
SQLALCHEMY_MAX_OVERFLOW = int(env.get("SQLALCHEMY_MAX_OVERFLOW", 10))
LOG_FORMAT = "text"

# Rate limiting - relaxed for development
RATE_LIMIT_LOGIN = "50/minute"
RATE_LIMIT_SIGNUP = "30/minute"
RATELIMIT_STORAGE_URI = env.get(
    "RATELIMIT_STORAGE_URI", "redis://redis:6379/0"
)
