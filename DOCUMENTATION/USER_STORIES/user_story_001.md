# US-001 — Rate Limiting on Authentication Endpoints

## Title

Implement Rate Limiting on Signup and Login Endpoints

## User Story

As a **security engineer**, I want to enforce rate limiting on the `/signup` and `/login` endpoints so that the API is protected against brute-force attacks and credential stuffing.

## Description

The rate limiter should support configurable thresholds per IP address (e.g., 5 login attempts per minute) and return HTTP 429 (Too Many Requests) when exceeded. Implementation should use `Flask-Limiter` backed by Redis for distributed rate tracking across Gunicorn workers.

### Key Requirements

- Configurable rate limits per endpoint (e.g., `5/minute` for login, `3/minute` for signup)
- Per-IP address tracking
- Redis backend for distributed state across multiple Gunicorn workers
- HTTP 429 response with `Retry-After` header when limit is exceeded
- Rate limit headers in all responses (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`)
- Environment-specific configuration (relaxed limits in dev/testing, strict in production)
- Whitelisting capability for trusted IPs

### Affected Components

- `core/users/routes/signup.py`
- `core/users/routes/login.py`
- `config/default.py` (new rate limit settings)
- `requirements.txt` / `pyproject.toml` (new dependencies)
- Docker Compose configs (Redis service)

## Priority

**Critical**

## Estimated Cost

**3 Story Points** (~1.5 days)

## Related Tasks

- [task_001_1.md](../TASKS/task_001_1.md) — Set up Redis and Flask-Limiter dependencies
- [task_001_2.md](../TASKS/task_001_2.md) — Implement rate limiting middleware
- [task_001_3.md](../TASKS/task_001_3.md) — Add rate limit configuration per environment
- [task_001_4.md](../TASKS/task_001_4.md) — Write unit and integration tests
- [task_001_5.md](../TASKS/task_001_5.md) — Update Docker Compose with Redis service

## Trello

[US-001 — Rate Limiting on Authentication Endpoints](https://trello.com/c/1EvHLJN2)
