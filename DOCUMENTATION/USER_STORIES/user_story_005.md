# US-005 — Health Check and Readiness Probes

## Title

Add Dedicated Health and Readiness Endpoints

## User Story

As a **DevOps engineer**, I want dedicated `/health` and `/ready` endpoints, so that container orchestrators and load balancers can determine application status.

## Description

The `/health` endpoint should return 200 if the process is alive (liveness probe). The `/ready` endpoint should verify database connectivity and external service availability before returning 200 (readiness probe). These endpoints should bypass authentication and CSRF.

### Key Requirements

- `GET /health` — liveness probe, returns `{"status": "ok"}` with HTTP 200 if application is running
- `GET /ready` — readiness probe, checks:
  - Database connectivity (execute a `SELECT 1` query)
  - External password scoring API availability (optional, with timeout)
  - SMTP server reachability (optional, with timeout)
- Returns `{"status": "ready", "checks": {...}}` with HTTP 200 if all checks pass
- Returns `{"status": "not_ready", "checks": {...}}` with HTTP 503 if any critical check fails
- No authentication or CSRF required on these endpoints
- Response time should not exceed 5 seconds (timeouts on dependency checks)

### Affected Components

- `core/users/routes/` (new `health.py` module)
- `core/users/__init__.py` (register new routes)
- `core/__init__.py` (CSRF exemption for health routes)
- Docker Compose files (healthcheck directives)

## Priority

**High**

## Estimated Cost

**2 Story Points** (~1 day)

## Related Tasks

- [task_005_1.md](../TASKS/task_005_1.md) — Implement /health liveness endpoint
- [task_005_2.md](../TASKS/task_005_2.md) — Implement /ready readiness endpoint with dependency checks
- [task_005_3.md](../TASKS/task_005_3.md) — Configure CSRF exemption for health routes
- [task_005_4.md](../TASKS/task_005_4.md) — Add Docker healthcheck directives
- [task_005_5.md](../TASKS/task_005_5.md) — Write tests for health endpoints

## Trello

[US-005 — Health Check and Readiness Probes](https://trello.com/c/U2lm1UtK)
