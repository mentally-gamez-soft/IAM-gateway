"""Load the configuration for production environment.

Raises:
    Exception: Raise an error if the .env file for production environment does not exist.
"""

from dotenv import load_dotenv

from .default import *

if not load_dotenv(join(ENV_DIR, ".env.prood")):
    raise Exception("Failed to load .env.prod file !!!")

DB_HOSTNAME = env.get("DB_HOSTNAME")
DB_PORT = env.get("DB_PORT")
DB_NAME = env.get("DB_NAME")
SQL_ALCHEMY_DATABASE_URI = env.get("SQL_ALCHEMY_DATABASE_URI")
SQLALCHEMY_DATABASE_SCHEMA = env.get("SQL_ALCHEMY_DATABASE_SCHEMA")
APP_ENV = APP_ENV_PRODUCTION
