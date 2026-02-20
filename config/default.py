"""Load the default configuration for all environments.

Raises:
    Exception: Raise an error if the .env file does not exist.
"""

from os import environ as env
from os.path import abspath, dirname, join

from dotenv import load_dotenv

# Define the application directory
BASE_DIR = dirname(dirname(abspath(__file__)))

ENV_DIR = join(BASE_DIR, "config")
JWT_ENV_DIR = join(ENV_DIR, "jwt")
APIS_ENV_DIR = join(ENV_DIR, "external_ws_apis")

if not load_dotenv(join(ENV_DIR, ".env")):
    raise Exception("Failed to load .env file !!!")

# Application information
APP_NAME = env.get("APP_NAME", "MyApp")
APP_VERSION = env.get("APP_VERSION", "0.0.1")
APP_USES_DATABASE = env.get("APP_USES_DATABASE", "True").lower() == "true"
APP_SEND_EMAILS = env.get("APP_SEND_EMAILS", "True").lower() == "true"

# logs files directories
LOG_PATH = join(BASE_DIR, env.get("LOG_PATH", "logs"))
LOG_FILENAME = env.get("LOG_FILENAME", "app.log")
# Logging format: "text" for human-readable, "json" for structured JSON
LOG_FORMAT = env.get("LOG_FORMAT", "text")

SECRET_KEY = env.get("SECRET_KEY")
SECURITY_PASSWORD_SALT = env.get("SECURITY_PASSWORD_SALT")
SQLALCHEMY_TRACK_MODIFICATIONS = (
    env.get("SQLALCHEMY_TRACK_MODIFICATIONS") == "True"
)

################################################################
# ### SQLAlchemy Connection Pool configuration             ####
################################################################
# pool_size: number of persistent connections kept open.
# max_overflow: additional connections allowed beyond pool_size.
# pool_recycle: seconds after which idle connections are replaced
#               (prevents stale connections after MySQL/PG firewall drops).
# pool_pre_ping: issue a lightweight ``SELECT 1`` before every checkout
#               to detect stale connections and replace them automatically.
# pool_timeout: seconds to wait for a connection before raising an error.
SQLALCHEMY_POOL_SIZE = int(env.get("SQLALCHEMY_POOL_SIZE", 5))
SQLALCHEMY_MAX_OVERFLOW = int(env.get("SQLALCHEMY_MAX_OVERFLOW", 10))
SQLALCHEMY_POOL_RECYCLE = int(env.get("SQLALCHEMY_POOL_RECYCLE", 1800))
SQLALCHEMY_POOL_PRE_PING = (
    env.get("SQLALCHEMY_POOL_PRE_PING", "True").lower() == "true"
)
SQLALCHEMY_POOL_TIMEOUT = int(env.get("SQLALCHEMY_POOL_TIMEOUT", 30))

# File uploads management
MAX_FILE_SIZE = env.get("MAX_FILE_SIZE", 16)  # defaults to 16 MB
MEDIA_DIR = join(BASE_DIR, env.get("MEDIA_DIR", "media"))
UPLOAD_DIR = join(MEDIA_DIR, env.get("UPLOAD_DIR", "uploads"))

# application environments
APP_ENV_LOCAL = env.get("APP_ENV_LOCAL")
APP_ENV_TESTING = env.get("APP_ENV_TESTING")
APP_ENV_DEVELOPMENT = env.get("APP_ENV_DEVELOPMENT")
APP_ENV_STAGING = env.get("APP_ENV_STAGING")
APP_ENV_PRODUCTION = env.get("APP_ENV_PRODUCTION")
APP_ENV = ""

# Email configuration
if APP_SEND_EMAILS:
    EMAIL_SERVER = env.get("EMAIL_SERVER")
    EMAIL_PORT = env.get("EMAIL_PORT")
    EMAIL_USERNAME = env.get("EMAIL_USERNAME")
    EMAIL_PASSWORD = env.get("EMAIL_PASSWORD")
    DONT_REPLY_FROM_EMAIL = tuple(env.get("DONT_REPLY_FROM_EMAIL").split(","))
    ADMINS = tuple(env.get("ADMINS").split(","))
    EMAIL_USE_TLS = env.get("EMAIL_USE_TLS") == "True"
    EMAIL_DEBUG = env.get("EMAIL_DEBUG") == "True"

# pagination
ITEMS_PER_PAGE = 15

DEBUG = False
TESTING = False
LOCAL_DEV = False
WTF_CSRF_ENABLED = True

# ###############  JWT ENCODINGS #########################
if not load_dotenv(join(JWT_ENV_DIR, ".env.jwt")):
    raise Exception("Failed to load .env.jwt file !!!")
ENCODING = env.get("ENCODING")
JWT_ALG = env.get("JWT_ALG")
JWT_EXPIRATION_TIME = env.get("JWT_EXPIRATION_TIME")
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
RULE_USERNAME_MIN_CHAR = int(env.get("RULE_USERNAME_MIN_CHAR"))
RULE_USERNAME_MAX_CHAR = int(env.get("RULE_USERNAME_MAX_CHAR"))
RULE_USERNAME_WITH_SPACES = env.get("RULE_USERNAME_WITH_SPACES")
RULE_PASSWORD_WITH_DIGITS = env.get("RULE_PASSWORD_WITH_DIGITS")
RULE_PASSWORD_WITH_LOWERCASE = env.get("RULE_PASSWORD_WITH_LOWERCASE")
RULE_PASSWORD_WITH_SPACES = env.get("RULE_PASSWORD_WITH_SPACES")
RULE_PASSWORD_WITH_SYMBOLS = env.get("RULE_PASSWORD_WITH_SYMBOLS")
RULE_PASSWORD_WITH_UPPERCASE = env.get("RULE_PASSWORD_WITH_UPPERCASE")
RULE_PASSWORD_MIN_LENGTH = int(env.get("RULE_PASSWORD_MIN_LENGTH"))
RULE_PASSWORD_MAX_LENGTH = int(env.get("RULE_PASSWORD_MAX_LENGTH"))
RULE_PASSWORD_MIN_STRENGTH_SCORE = int(
    env.get("RULE_PASSWORD_MIN_STRENGTH_SCORE")
)

# Resilience pattern params for external APIs and WS
CIRCUIT_BREAKER_MAX_FAIL = int(env.get("CIRCUIT_BREAKER_MAX_FAIL", 5))
CIRCUIT_BREAKER_RESET_TIMEOUT = int(
    env.get("CIRCUIT_BREAKER_RESET_TIMEOUT", 120)
)
RETRY_CALLS = int(env.get("RETRY_CALLS", 3))

################################################################
# ### Rate Limiting configuration                           ####
################################################################
RATELIMIT_STORAGE_URI = env.get(
    "RATELIMIT_STORAGE_URI", "redis://redis:6379/0"
)
RATE_LIMIT_LOGIN = env.get("RATE_LIMIT_LOGIN", "5/minute")
RATE_LIMIT_SIGNUP = env.get("RATE_LIMIT_SIGNUP", "3/minute")
RATE_LIMIT_DEFAULT = env.get("RATE_LIMIT_DEFAULT", "200/hour")
RATE_LIMIT_FORGOT_PASSWORD = env.get("RATE_LIMIT_FORGOT_PASSWORD", "3/hour")

################################################################
# ### Password Reset configuration                         ####
################################################################
PASSWORD_RESET_TOKEN_EXPIRATION = int(
    env.get("PASSWORD_RESET_TOKEN_EXPIRATION", 1800)
)  # 30 minutes in seconds
PASSWORD_RESET_EMAIL_SUBJECT = env.get(
    "PASSWORD_RESET_EMAIL_SUBJECT", "Reset Your Password"
)
PASSWORD_RESET_SALT = env.get("PASSWORD_RESET_SALT", "password-reset-salt")

################################################################
# ### JWT Token Refresh configuration                      ####
################################################################
JWT_ACCESS_TOKEN_LIFETIME = int(
    env.get("JWT_ACCESS_TOKEN_LIFETIME", 15)
)  # 15 minutes default
JWT_REFRESH_TOKEN_LIFETIME = int(
    env.get("JWT_REFRESH_TOKEN_LIFETIME", 10080)
)  # 7 days (10080 minutes) default

################################################################
# ### CORS configuration                                   ####
################################################################
# CORS_ORIGINS: list of allowed origins, or "*" for all.
# Supports a comma-separated string when provided via env var so
# it can be overridden in .env files without redeploying.
_cors_origins_raw: str = env.get("CORS_ORIGINS", "*")
if _cors_origins_raw.strip() == "*":
    CORS_ORIGINS = "*"
else:
    CORS_ORIGINS = [
        o.strip() for o in _cors_origins_raw.split(",") if o.strip()
    ]

CORS_METHODS: list = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
CORS_ALLOW_HEADERS: list = [
    "Content-Type",
    "Authorization",
    "X-CSRFToken",
    "X-Request-ID",
]
CORS_EXPOSE_HEADERS: list = [
    "X-CSRFToken",
    "X-RateLimit-Limit",
    "X-RateLimit-Remaining",
]
CORS_SUPPORTS_CREDENTIALS: bool = True
CORS_MAX_AGE: int = 600  # preflight cache — 10 minutes

################################################################
# ### API with token auth. CSRF protection disabled   ##########
################################################################
WTF_CSRF_ENABLED = False
