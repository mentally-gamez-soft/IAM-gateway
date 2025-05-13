"""Load the configuration for development environment.

Raises:
    Exception: Raise an error if the .env file for development environment does not exist.
"""

from dotenv import load_dotenv

from .default import *

if not load_dotenv(join(ENV_DIR, ".env.dev")):
    raise Exception("Failed to load .env.dev file !!!")

SQL_ALCHEMY_DATABASE_URI = env.get("SQL_ALCHEMY_DATABASE_URI")
APP_ENV = APP_ENV_DEVELOPMENT
DEBUG = True
