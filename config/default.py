"""Load the default configuration for all environments.

Raises:
    Exception: Raise an error if the .env file does not exist.
"""

from os import environ as env
from os.path import abspath, dirname, join

from dotenv import load_dotenv

BASE_DIR = dirname(dirname(abspath(__file__)))
ENV_DIR = join(BASE_DIR, "config")
JWT_ENV_DIR = join(ENV_DIR, "jwt")
APIS_ENV_DIR = join(ENV_DIR, "external_ws_apis")

if not load_dotenv(join(ENV_DIR, ".env")):
    raise Exception("Failed to load .env file !!!")

SECRET_KEY = env.get("SECRET_KEY")
SECURITY_PASSWORD_SALT = env.get("SECURITY_PASSWORD_SALT")
SQLALCHEMY_TRACK_MODIFICATIONS = (
    env.get("SQLALCHEMY_TRACK_MODIFICATIONS") == "True"
)

# application environments
APP_ENV_LOCAL = "local"
APP_ENV_TESTING = "testing"
APP_ENV_DEVELOPMENT = "development"
APP_ENV_STAGING = "staging"
APP_ENV_PRODUCTION = "production"
APP_ENV = ""

# Email configuration
MAIL_SERVER = env.get("MAIL_SERVER")
MAIL_PORT = env.get("MAIL_PORT")
MAIL_USERNAME = env.get("MAIL_USERNAME")
MAIL_PASSWORD = env.get("MAIL_PASSWORD")
DONT_REPLY_FROM_EMAIL = env.get("DONT_REPLY_FROM_EMAIL")
ADMINS = env.get("ADMINS")
MAIL_USE_TLS = True
MAIL_DEBUG = env.get("MAIL_DEBUG") == "True"

# pagination
ITEMS_PER_PAGE = 10

DEBUG = False

# ###############  JWT ENCODINGS #########################
if not load_dotenv(join(JWT_ENV_DIR, ".env.jwt")):
    raise Exception("Failed to load .env.jwt file !!!")
ENCODING = env.get("ENCODING")
JWT_ALG = env.get("JWT_ALG")
JWT_ENCODING_PARAM_1 = env.get("JWT_ENCODING_PARAM_1")
JWT_ENCODING_PARAM_2 = env.get("JWT_ENCODING_PARAM_2")
JWT_ENCODING_PARAM_3 = env.get("JWT_ENCODING_PARAM_3")

################################################################
# ### loading configurations for external services from here ###
################################################################
# ###############  API SCORING PASWORD #########################
if not load_dotenv(join(APIS_ENV_DIR, ".env.api_scoring_password")):
    raise Exception(
        "Failed to load .env file for the password scoring api !!!"
    )

WS_SCORING_PASSWORD_URL_API = env.get("WS_SCORING_PASSWORD_URL_API")
RULE_USERNAME_MIN_CHAR = env.get("RULE_USERNAME_MIN_CHAR")
RULE_USERNAME_MAX_CHAR = env.get("RULE_USERNAME_MAX_CHAR")
RULE_USERNAME_WITH_SPACES = env.get("RULE_USERNAME_WITH_SPACES")
RULE_PASSWORD_WITH_DIGITS = env.get("RULE_PASSWORD_WITH_DIGITS")
RULE_PASSWORD_WITH_LOWERCASE = env.get("RULE_PASSWORD_WITH_LOWERCASE")
RULE_PASSWORD_WITH_SPACES = env.get("RULE_PASSWORD_WITH_SPACES")
RULE_PASSWORD_WITH_SYMBOLS = env.get("RULE_PASSWORD_WITH_SYMBOLS")
RULE_PASSWORD_WITH_UPPERCASE = env.get("RULE_PASSWORD_WITH_UPPERCASE")
RULE_PASSWORD_MIN_LENGTH = env.get("RULE_PASSWORD_MIN_LENGTH")
RULE_PASSWORD_MAX_LENGTH = env.get("RULE_PASSWORD_MAX_LENGTH")
RULE_PASSWORD_MIN_STRENGTH_SCORE = env.get("RULE_PASSWORD_MIN_STRENGTH_SCORE")
