# IAM-gateway
gateway portal for users login/logout
and discovery service

The web service is ready for executing in the following environment:
- local development
- containerized docker host development
- containerized docker host production ready (gunicorn and nginx)

A set of tools is provided to help you to create, run and stop the docker container.

## Requirements
- Python 3.11 or higher
- pip 24.0 or higher
- virtualenv 20.16.7 or higher
- uv 0.4.0 or higher
- docker 20.10.21 or higher
- docker-compose 1.29.2 or higher

## Stack Technologies
![Alt text](technology_stack_IAM-GW.svg)

## API Endpoints
### Sanity check
    The check is located at home "/"

### Signup
    The signup endpoint is located at "/signup"

### Login
    The login endpoint is located at "/login"

### Logout
    The logout endpoint is located at "/logout"

### Activation account
    The activation account endpoint is located at "/confirm/<token>"

### Forgot password
    The forgot password endpoint is located at "/forgot-password"
    Request: POST /forgot-password with {"email": "user@example.com"}
    Always returns 200 for security (prevents email enumeration)
    Rate limited to 3 requests per hour

### Reset password
    The reset password endpoint is located at "/reset-password/<token>"
    Request: POST /reset-password/<token> with {"new_password": "..."}
    Validates token expiration (30 minutes by default)
    Requires password strength validation
    Clears JWT session to force re-login

### Refresh Token
    The token refresh endpoint is located at "/token/refresh"
    Request: POST /token/refresh with refresh token in Authorization header or Body
    Returns new access_token (15 min expiration) + refresh_token (7 days expiration)
    Supports token rotation with family tracking for security breach detection
    Replayed/revoked tokens trigger family-wide revocation (401 response)
    Tokens stored securely in database with SHA-256 hashing

### Dual-Token System
    Login now returns both a short-lived access token (15 minutes) and a long-lived refresh token (7 days)
    Access token: Used for API authentication via Authorization Bearer header
    Refresh token: Used to obtain new access tokens via /token/refresh endpoint
    Token rotation: Old refresh tokens are marked with replaced_by relationship
    Family ID tracking: Detects and prevents token reuse attacks

### Health Check — Liveness Probe (US-005)
    GET /health — returns 200 if the application process is alive (no DB, no auth required)
    Response: {"status": "ok", "timestamp": "<ISO 8601>", "version": "<APP_VERSION>"}
    Use as Docker/Kubernetes liveness probe target.

### Readiness Probe (US-005)
    GET /ready — returns 200 when all critical dependencies are reachable; 503 otherwise
    Checks performed:
        - database: executes SELECT 1 via SQLAlchemy (3-second timeout)
        - password_api: HTTP HEAD to WS_SCORING_PASSWORD_URL_API (3-second timeout; skipped if URL is empty)
        - smtp: TCP connect to SMTP server (3-second timeout; skipped if APP_SEND_EMAILS=False)
    Response: {"status": "ready"|"not_ready", "checks": {"database": {...}, "password_api": {...}, "smtp": {...}}}
    Both endpoints bypass authentication and CSRF protection.
    Docker HEALTHCHECK is configured in Dockerfile and both compose files using wget --spider http://localhost:5000/health

## Structured JSON Logging (US-004)

The application supports two log output formats controlled by the `LOG_FORMAT` environment variable:

| `LOG_FORMAT` | Environments | Output |
|---|---|---|
| `text` (default) | local, dev, testing | Human-readable coloured text |
| `json` | staging, production | Structured JSON, one object per line |

### JSON log fields

Every log entry in JSON mode includes:

| Field | Description |
|---|---|
| `timestamp` | ISO 8601 UTC timestamp |
| `level` | Log level name (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `logger` | Logger name |
| `function` | Calling function name |
| `lineno` | Source line number |
| `environment` | Value of `APP_ENV` config |
| `message` | Log message |
| `request_id` | UUID from `X-Request-ID` header or auto-generated per request |
| `user_id` | Authenticated user ID (null if anonymous) |
| `remote_addr` | Client IP address |
| `method` | HTTP method |
| `path` | Request path |

### Request ID propagation

Pass `X-Request-ID: <uuid>` in the request header to correlate log entries with your upstream tracing system. If the header is absent, a UUID v4 is generated automatically and stored in `flask.g.request_id`.

### Swagger documentations
    The swagger UI is located at "/swagger"

## Display environment variables
    display all env variables:
    gci env:* | sort-object name

## Set the environment variables

    On unix OS:
     - export FLASK_APP="application"
     - export FLASK_ENV="development"
     - export APP_SETTINGS_MODULE="config.local"
     - export FLASK_DEBUG=1

    On Windows OS powershell:
     - $env:FLASK_APP="application"
     - $env:FLASK_ENV="development"
     - $env:APP_SETTINGS_MODULE="config.local"
     - $env:FLASK_DEBUG = "1"

## Running application
## Local development

    uv run -m flask --app application run --port 3456 --host 0.0.0.0

### Executing the tests suit
    uv run -m unittest tests.test_standard_routes
    uv run -m unittest tests.test_health

### Executing database migrations:
    flask --app application db init
    flask --app application db migrate -m "initial migrations"
    flask --app application db upgrade

## Docker Images
### Create an image
    On unix OS:
    execute the shell ./docker_manager.sh choose option (1) and follow the instructions.

    On windows OS:
    execute the shell ./docker_manager.ps1 choose option (1) and follow the instructions.

### Run a container
    On unix OS:
    execute the shell ./docker_manager.sh choose option (2) and follow the instructions.

    On windows OS:
    execute the shell ./docker_manager.ps1 choose option (2) and follow the instructions.

### Stop a container
    On unix OS:
    execute the shell ./docker_manager.sh choose option (3) and follow the instructions.

    On windows OS:
    execute the shell ./docker_manager.ps1 choose option (3) and follow the instructions.
