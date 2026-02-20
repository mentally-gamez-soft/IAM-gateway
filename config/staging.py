"""Load the configuration for staging environment.

Raises:
    Exception: Raise an error if the .env file for staging environment does not exist.
"""

from dotenv import load_dotenv

from .default import *

if not load_dotenv(join(ENV_DIR, ".env.staging")):
    raise Exception("Failed to load .env.staging file !!!")

DB_HOSTNAME = env.get("DB_HOSTNAME")
DB_PORT = env.get("DB_PORT")
DB_NAME = env.get("DB_NAME")
SQLALCHEMY_DATABASE_URI = env.get("SQLALCHEMY_DATABASE_URI")
SQLALCHEMY_DATABASE_SCHEMA = env.get("SQLALCHEMY_DATABASE_SCHEMA")
APP_ENV = APP_ENV_STAGING
LOG_FORMAT = "json"

# Connection pool — elevated capacity for staging load tests
SQLALCHEMY_POOL_SIZE = int(env.get("SQLALCHEMY_POOL_SIZE", 10))
SQLALCHEMY_MAX_OVERFLOW = int(env.get("SQLALCHEMY_MAX_OVERFLOW", 15))

# CORS — staging frontend origin (override via CORS_ORIGINS env var)
CORS_ORIGINS = (
    env.get("CORS_ORIGINS", "https://staging.example.com").split(",")
    if env.get("CORS_ORIGINS", "https://staging.example.com").strip() != "*"
    else "*"
)

# Rate limiting - moderate for staging
RATE_LIMIT_LOGIN = "10/minute"
RATE_LIMIT_SIGNUP = "5/minute"
RATELIMIT_STORAGE_URI = env.get(
    "RATELIMIT_STORAGE_URI", "redis://redis:6379/0"
)
