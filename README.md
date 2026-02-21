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

> **API Version**: All endpoints are now prefixed with `/api/v1/` (US-006).  
> Legacy unversioned routes (e.g. `/login`) remain available until **2026-09-01** with deprecation headers.  
> See [DOCUMENTATION/API_MIGRATION_GUIDE.md](DOCUMENTATION/API_MIGRATION_GUIDE.md) for the full migration guide.

### Sanity check
    The check is located at "/api/v1/"

### Signup
    The signup endpoint is located at "POST /api/v1/signup"
    Legacy: POST /signup (deprecated — sunset 2026-09-01)

### Login
    The login endpoint is located at "POST /api/v1/login"
    Legacy: POST /login (deprecated — sunset 2026-09-01)
    Response now includes access_token, refresh_token, token_type, expires_in

### Logout
    The logout endpoint is located at "POST /api/v1/logout"
    Legacy: POST /logout (deprecated — sunset 2026-09-01)

### Activation account
    The activation account endpoint is located at "GET /api/v1/confirm/<token>"
    Legacy: GET /confirm/<token> (deprecated — sunset 2026-09-01)

### Forgot password
    The forgot password endpoint is located at "POST /api/v1/forgot-password"
    Legacy: POST /forgot-password (deprecated — sunset 2026-09-01)
    Always returns 200 for security (prevents email enumeration)
    Rate limited to 3 requests per hour

### Reset password
    The reset password endpoint is located at "POST /api/v1/reset-password/<token>"
    Legacy: POST /reset-password/<token> (deprecated — sunset 2026-09-01)
    Validates token expiration (30 minutes by default)
    Requires password strength validation
    Clears JWT session to force re-login

### Refresh Token
    The token refresh endpoint is located at "POST /api/v1/token/refresh"
    Legacy: POST /token/refresh (deprecated — sunset 2026-09-01)
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

### User Profile Management (US-011)

    GET /profile — returns the authenticated user's profile data
    PUT /profile — updates mutable profile fields for the authenticated user

Both endpoints require authentication (`authorization_guard`, `login_required`).
The request body must include `access_token` (or legacy `jwt`) and `user` inside a `data` object.

#### Profile fields

| Field | Type | Updatable via PUT | Description |
|---|---|---|---|
| `id` | UUID | No | User identifier |
| `username` | String | No | Login username (immutable via this endpoint) |
| `email` | String | No | Login email (immutable via this endpoint) |
| `display_name` | String ≤80 | **Yes** | Optional public display name |
| `avatar_url` | String ≤255 | **Yes** | URL to avatar image |
| `bio` | Text | **Yes** | Free-form biography |
| `language_preference` | String 2-5 | **Yes** | Locale code (e.g. `en`, `fr`) |
| `timezone` | String ≤50 | **Yes** | IANA timezone (e.g. `UTC`, `Europe/Paris`) |
| `profile_updated_at` | DateTime | Auto | Set automatically on each PUT |

#### curl examples

```bash
# GET profile
curl -s -X GET http://localhost:5000/profile \
  -H "Content-Type: application/json" \
  -d '{"data":{"access_token":"<JWT>","user":"<base64-user-id>"}}'

# PUT profile
curl -s -X PUT http://localhost:5000/profile \
  -H "Content-Type: application/json" \
  -d '{
    "data":{
      "access_token":"<JWT>",
      "user":"<base64-user-id>",
      "profile":{"display_name":"Alice","language_preference":"fr","timezone":"Europe/Paris"}
    }
  }'
```

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

## Database Connection Pooling (US-007)

SQLAlchemy engine options are automatically built from the `SQLALCHEMY_POOL_*`
config variables and applied before `db.init_app()`.

### Per-environment defaults

| Environment | `SQLALCHEMY_POOL_SIZE` | `SQLALCHEMY_MAX_OVERFLOW` |
|-------------|----------------------|--------------------------|
| local       | 3                    | 5                        |
| testing     | 2                    | 3                        |
| dev         | 5                    | 10                       |
| staging     | 10                   | 15                       |
| prod        | 15                   | 25                       |

Common settings (all environments, overridable via `.env.*` files):

| Variable                   | Default | Description                                      |
|----------------------------|---------|--------------------------------------------------|
| `SQLALCHEMY_POOL_PRE_PING` | `True`  | Issue `SELECT 1` on each checkout to detect stale connections |
| `SQLALCHEMY_POOL_RECYCLE`  | `1800`  | Recycle idle connections after 30 minutes        |
| `SQLALCHEMY_POOL_TIMEOUT`  | `30`    | Seconds to wait for a free connection            |

> **SQLite** (local/testing) uses `StaticPool`/`NullPool` which do not support
> `pool_size` or `max_overflow`.  For SQLite the only option applied is
> `pool_pre_ping`.

### Pool metrics at `/ready`

`GET /ready` exposes real-time pool statistics under `checks.database.pool`:

```json
{
  "checks": {
    "database": {
      "status": "ok",
      "pool": {
        "available": true,
        "pool_size": 2,
        "checked_out": 1,
        "checked_in": 1,
        "overflow": 0,
        "max_overflow": 3,
        "utilization_pct": 33.3,
        "saturated": false
      }
    }
  }
}
```

`saturated: true` is set when utilization exceeds 80 %.

---

## CORS Configuration (US-009)

The gateway uses [Flask-CORS](https://flask-cors.readthedocs.io/) to add
`Access-Control-*` headers to every API response, enabling browser-based
clients to call the API across origins.

### Per-environment allowed origins

| Environment | `CORS_ORIGINS` |
|---|---|
| `local` | `*` (all origins) |
| `dev` | `*` (all origins) |
| `testing` | `*` (all origins) |
| `staging` | `https://staging.example.com` |
| `prod` | `https://app.example.com` |

Override with the `CORS_ORIGINS` environment variable (comma-separated list or
`*`).

### CORS settings

| Variable | Default | Description |
|---|---|---|
| `CORS_ORIGINS` | `*` | Allowed origin(s) — `*` or a comma-separated list of URLs |
| `CORS_METHODS` | `GET,POST,PUT,DELETE,OPTIONS` | Allowed HTTP methods |
| `CORS_ALLOW_HEADERS` | `Content-Type,Authorization,X-CSRFToken,X-Request-ID` | Headers allowed on requests |
| `CORS_EXPOSE_HEADERS` | `X-CSRFToken,X-RateLimit-Limit,X-RateLimit-Remaining` | Headers exposed to the browser |
| `CORS_SUPPORTS_CREDENTIALS` | `True` | `Access-Control-Allow-Credentials` |
| `CORS_MAX_AGE` | `600` | Preflight cache duration in seconds |

### Manual curl verification

```bash
# --- 1. Simple GET — check Allow-Origin response header ---
curl -i -H "Origin: http://localhost:3000" \
     http://localhost:3456/health

# --- 2. OPTIONS preflight — check all CORS headers ---
curl -i -X OPTIONS \
     -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type,Authorization" \
     http://localhost:3456/health

# --- 3. Verify Access-Control-Allow-Credentials: true ---
curl -s -o /dev/null -D - \
     -H "Origin: http://localhost:3000" \
     http://localhost:3456/health \
  | grep -i "Access-Control"

# --- 4. Readiness probe also includes CORS headers ---
curl -i -H "Origin: http://localhost:3000" \
     http://localhost:3456/ready

# --- 5. CORS headers present on 404 responses ---
curl -i -H "Origin: http://localhost:3000" \
     http://localhost:3456/does-not-exist
```

**Expected headers** on any response:

```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Credentials: true
Access-Control-Expose-Headers: X-CSRFToken, X-RateLimit-Limit, X-RateLimit-Remaining
```

**Expected headers** on a preflight `OPTIONS` response:

```
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization, X-CSRFToken, X-Request-ID
Access-Control-Allow-Credentials: true
Access-Control-Max-Age: 600
```

## Running application
## Local development

    uv run -m flask --app application run --port 3456 --host 0.0.0.0

    APP_SETTINGS_MODULE="config.local" \
    FLASK_DEBUG=1 \
    FLASK_APP="application" \
    FLASK_ENV="development" \
    uv run -m flask --app application run --port 3456 --host 0.0.0.0

### Executing the tests suit
    uv run -m unittest tests.test_standard_routes
    uv run -m unittest tests.test_health

### Running Database Migrations

The migration runner (`migrations/env.py`) automatically selects the correct
database connection based on the `APP_SETTINGS_MODULE` environment variable.
The Flask application context takes priority; if it is not available (e.g. in a
CI/CD pipeline or a bare Alembic invocation) the config module is imported
directly to resolve `SQLALCHEMY_DATABASE_URI`.

**Initialise migration structure (first time only)**

    flask --app application db init

**Generate a new migration script (autogenerate)**

    # local
    APP_SETTINGS_MODULE="config.local" uv run -m flask --app application db migrate -m "description"

    # dev
    APP_SETTINGS_MODULE="config.dev"   uv run -m flask --app application db migrate -m "description"

**Apply pending migrations**

    # local
    APP_SETTINGS_MODULE="config.local"   uv run -m flask --app application db upgrade

    # dev
    APP_SETTINGS_MODULE="config.dev"     uv run -m flask --app application db upgrade

    # staging
    APP_SETTINGS_MODULE="config.staging" uv run -m flask --app application db upgrade

    # production
    APP_SETTINGS_MODULE="config.prod"    uv run -m flask --app application db upgrade

**Standalone Alembic (no Flask app required)**

    APP_SETTINGS_MODULE="config.local" uv run -m alembic upgrade head
    APP_SETTINGS_MODULE="config.dev"   uv run -m alembic upgrade head

> **Note:** `APP_SETTINGS_MODULE` must be set, and all environment variables
> referenced by the selected config module (e.g. `SQLALCHEMY_DATABASE_URI`)
> must be available (loaded from the corresponding `.env.*` file or set
> directly in the shell).

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
