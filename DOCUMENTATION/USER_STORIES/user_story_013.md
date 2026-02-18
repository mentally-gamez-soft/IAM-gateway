# US-013 — Centralized Error Handling with Correlation IDs

## Title

Add Request Correlation IDs and Standardized Error Responses

## User Story

As a **DevOps engineer**, I want every API request to carry a unique correlation ID (`X-Request-ID`), so that I can trace requests across logs and services.

## Description

All error responses should follow a consistent JSON schema: `{"error": {"code": "...", "message": "...", "request_id": "..."}}`. A middleware should generate or propagate the `X-Request-ID` header and attach it to the Flask `g` object for use in logging and responses.

### Key Requirements

- Before-request middleware that:
  - Reads `X-Request-ID` from incoming request headers (if present)
  - Generates a new UUID if not present
  - Stores the ID in Flask `g.request_id`
- After-request middleware that:
  - Adds `X-Request-ID` header to all responses
- Standardized error response format: `{"error": {"code": "<HTTP_CODE>", "message": "<description>", "request_id": "<uuid>"}}`
- Update all error handlers (400, 401, 403, 404, 422, 500) with the new format
- Integrate `request_id` into logging context (visible in all log lines for a request)
- Update existing route error responses to use the standardized format

### Affected Components

- `core/__init__.py` (before/after request hooks, error handlers)
- `core/users/routes/*.py` (standardize error response format)
- `core/common/error_codes.py` (centralized error code definitions)
- `server/config/logs.py` (add `request_id` to log formatter)

## Priority

**Medium**

## Estimated Cost

**3 Story Points** (~1.5 days)

## Related Tasks

- [task_013_1.md](../TASKS/task_013_1.md) — Implement request ID middleware (before/after request)
- [task_013_2.md](../TASKS/task_013_2.md) — Standardize error response format across all handlers
- [task_013_3.md](../TASKS/task_013_3.md) — Integrate request_id into logging context
- [task_013_4.md](../TASKS/task_013_4.md) — Update route error responses to standardized format
- [task_013_5.md](../TASKS/task_013_5.md) — Write tests for correlation ID propagation and error format

## Trello

[US-013 — Request Correlation ID Tracking](https://trello.com/c/9614J13Z)
