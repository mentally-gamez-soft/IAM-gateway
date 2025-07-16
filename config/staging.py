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
