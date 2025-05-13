"""Load the configuration for staging environment.

Raises:
    Exception: Raise an error if the .env file for staging environment does not exist.
"""

from dotenv import load_dotenv

from .default import *

if not load_dotenv(join(ENV_DIR, ".env.staging")):
    raise Exception("Failed to load .env.staging file !!!")

SQL_ALCHEMY_DATABASE_URI = env.get("SQL_ALCHEMY_DATABASE_URI")
APP_ENV = APP_ENV_STAGING
