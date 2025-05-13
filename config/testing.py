"""Load the configuration for testing environment.

Raises:
    Exception: Raise an error if the .env file for testing environment does not exist.
"""

from dotenv import load_dotenv

from .default import *

if not load_dotenv(join(ENV_DIR, ".env.testing")):
    raise Exception("Failed to load .env.testing file !!!")

SQL_ALCHEMY_DATABASE_URI = env.get("SQL_ALCHEMY_DATABASE_URI")
APP_ENV = APP_ENV_TESTING
DEBUG = True
TESTING = True
WTF_CSRF_ENABLED = False
