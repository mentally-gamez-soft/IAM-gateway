# US-006 — API Versioning Strategy

## Title

Implement Consistent API Versioning via URL Prefix

## User Story

As an **API consumer**, I want the API to follow a consistent versioning scheme (e.g., `/api/v1/...`), so that breaking changes can be introduced in new versions without affecting existing clients.

## Description

Currently, routes are duplicated (e.g., `/signup` and `/<app>/api/<version>/signup`). The API should standardize on a single versioned URL pattern using Flask Blueprints with a `url_prefix`. Legacy unversioned routes should be deprecated with appropriate HTTP `Deprecation` headers.

### Key Requirements

- All endpoints accessible under `/api/v1/` prefix (e.g., `/api/v1/signup`, `/api/v1/login`)
- Version defined via Flask Blueprint `url_prefix` parameter
- Legacy unversioned routes (`/signup`, `/login`, etc.) kept temporarily with `Deprecation` HTTP header
- Swagger documentation updated to reflect versioned routes
- API version extractable from URL for logging and metrics
- Architecture ready to support `/api/v2/` in the future without breaking v1

### Affected Components

- `core/users/__init__.py` (Blueprint `url_prefix`)
- `core/users/routes/*.py` (remove duplicated route definitions)
- `core/swagger/swagger_config.py` (update API URL)
- `static/swagger-docs/swagger.json` (update paths)
- `tests/test_standard_routes.py` (update test URLs)

## Priority

**High**

## Estimated Cost

**3 Story Points** (~1.5 days)

## Related Tasks

- [task_006_1.md](../TASKS/task_006_1.md) — Restructure Blueprint with versioned URL prefix
- [task_006_2.md](../TASKS/task_006_2.md) — Add deprecation headers to legacy routes
- [task_006_3.md](../TASKS/task_006_3.md) — Update Swagger configuration for versioned paths
- [task_006_4.md](../TASKS/task_006_4.md) — Update all tests to use versioned routes
- [task_006_5.md](../TASKS/task_006_5.md) — Document migration guide for API consumers

## Trello

[US-006 — API Versioning Strategy](https://trello.com/c/MHNvwFUO)
