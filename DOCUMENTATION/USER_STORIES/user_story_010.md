# US-010 — OpenAPI Specification Auto-Generation

## Title

Auto-Generate OpenAPI/Swagger Spec from Code

## User Story

As an **API consumer**, I want the Swagger documentation to be auto-generated from the codebase (docstrings and type hints), so that documentation stays in sync with the implementation.

## Description

Currently, the Swagger spec is a static JSON file (`static/swagger-docs/swagger.json`). Migrate to `flask-smorest` or `apispec` with `marshmallow` schemas to generate the OpenAPI 3.0 spec dynamically.

### Key Requirements

- Replace static `swagger.json` with auto-generated OpenAPI 3.0 specification
- Define `marshmallow` schemas for all request/response payloads
- Annotate each route with schema decorators for automatic spec generation
- Swagger UI served from the auto-generated spec (no manual JSON maintenance)
- API info (title, version, description) sourced from application config
- Authentication scheme documented in the spec (JWT Bearer + CSRF)
- Error response schemas standardized and documented

### Affected Components

- `pyproject.toml` / `requirements.txt` (add `flask-smorest`, `marshmallow`)
- `core/users/routes/*.py` (annotate routes with schemas)
- `core/swagger/swagger_config.py` (replace static config with dynamic generation)
- `static/swagger-docs/swagger.json` (to be deprecated/removed)
- New `core/schemas/` directory for marshmallow schemas
- `core/users/forms.py` (potentially migrate to marshmallow schemas)

## Priority

**Medium**

## Estimated Cost

**5 Story Points** (~2.5 days)

## Related Tasks

- [task_010_1.md](../TASKS/task_010_1.md) — Install flask-smorest and marshmallow dependencies
- [task_010_2.md](../TASKS/task_010_2.md) — Create marshmallow schemas for all payloads
- [task_010_3.md](../TASKS/task_010_3.md) — Annotate route endpoints with schema decorators
- [task_010_4.md](../TASKS/task_010_4.md) — Replace static Swagger config with dynamic generation
- [task_010_5.md](../TASKS/task_010_5.md) — Validate generated spec and update Swagger UI
- [task_010_6.md](../TASKS/task_010_6.md) — Write tests verifying spec accuracy

## Trello

[US-010 — OpenAPI Specification Auto-Generation](https://trello.com/c/S6Tzir2x)
