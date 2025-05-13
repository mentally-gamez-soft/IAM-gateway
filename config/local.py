"""Load the configuration for local environment.

Raises:
    Exception: Raise an error if the .env file for local environment does not exist.
"""

from dotenv import load_dotenv

from .default import *

if not load_dotenv(join(ENV_DIR, ".env.local")):
    raise Exception("Failed to load .env.local file !!!")

SQL_ALCHEMY_DATABASE_URI = env.get("SQL_ALCHEMY_DATABASE_URI")
APP_ENV = APP_ENV_LOCAL
DEBUG = True
