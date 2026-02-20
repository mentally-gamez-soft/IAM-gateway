"""Load the configuration for production environment.

Raises:
    Exception: Raise an error if the .env file for production environment does not exist.
"""

from dotenv import load_dotenv

from .default import *

if not load_dotenv(join(ENV_DIR, ".env.prod")):
    raise Exception("Failed to load .env.prod file !!!")

DB_HOSTNAME = env.get("DB_HOSTNAME")
DB_PORT = env.get("DB_PORT")
DB_NAME = env.get("DB_NAME")
SQLALCHEMY_DATABASE_URI = env.get("SQLALCHEMY_DATABASE_URI")
SQLALCHEMY_DATABASE_SCHEMA = env.get("SQLALCHEMY_DATABASE_SCHEMA")
APP_ENV = APP_ENV_PRODUCTION
LOG_FORMAT = "json"

# Connection pool — high capacity for production traffic
SQLALCHEMY_POOL_SIZE = int(env.get("SQLALCHEMY_POOL_SIZE", 15))
SQLALCHEMY_MAX_OVERFLOW = int(env.get("SQLALCHEMY_MAX_OVERFLOW", 25))

# Rate limiting - strict for production
RATE_LIMIT_LOGIN = "5/minute"
RATE_LIMIT_SIGNUP = "3/minute"
RATELIMIT_STORAGE_URI = env.get(
    "RATELIMIT_STORAGE_URI", "redis://redis:6379/0"
)
