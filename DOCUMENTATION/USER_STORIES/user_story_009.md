# US-009 — CORS Configuration

## Title

Add Configurable CORS Support

## User Story

As a **frontend developer**, I want the API to include proper CORS headers, so that browser-based clients from allowed origins can call the API without cross-origin errors.

## Description

The implementation should use `Flask-CORS` with environment-specific allowed origins, methods, and headers. Production should restrict origins to known frontend domains only.

### Key Requirements

- Install and configure `Flask-CORS` extension
- Environment-specific allowed origins:
  - Local/Dev: `*` (all origins allowed)
  - Staging: specific staging frontend URLs
  - Production: strictly whitelisted production frontend domains
- Allowed methods: `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS`
- Allowed headers: `Content-Type`, `Authorization`, `X-CSRFToken`, `X-Request-ID`
- Expose headers: `X-CSRFToken`, `X-RateLimit-Limit`, `X-RateLimit-Remaining`
- `Access-Control-Max-Age`: 600 seconds (preflight cache)
- Credentials support (`supports_credentials=True`)

### Affected Components

- `pyproject.toml` / `requirements.txt` (add `flask-cors`)
- `core/__init__.py` (initialize CORS in app factory)
- `config/default.py` (CORS default settings)
- `config/local.py`, `config/dev.py`, `config/staging.py`, `config/prod.py` (environment-specific origins)

## Priority

**Medium**

## Estimated Cost

**1 Story Point** (~0.5 day)

## Related Tasks

- [task_009_1.md](../TASKS/task_009_1.md) — Install Flask-CORS and configure in app factory
- [task_009_2.md](../TASKS/task_009_2.md) — Add environment-specific CORS origins configuration
- [task_009_3.md](../TASKS/task_009_3.md) — Write tests for CORS headers in responses

## Trello

[US-009 — CORS Configuration](https://trello.com/c/25GQjdYC)
