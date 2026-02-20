```markdown
# US-018 — Environment-Aware Database Migrations

## Title

Make Database Migration Scripts Dynamically Select the Correct Database Connection Based on Environment

## User Story

As a **developer**, I want the Alembic migration scripts to automatically read the `APP_SETTINGS_MODULE` environment variable and resolve the correct database connection string, so that I can run migrations in any environment without manually editing migration configuration files.

## Description

Currently, `migrations/env.py` relies exclusively on Flask's `current_app` context (provided by Flask-Migrate) to obtain the database connection URL. This works well when running `flask db upgrade` inside an active Flask application context, but becomes fragile in CI/CD pipelines, Docker entrypoints, or standalone Alembic runs where the application context may not be available or is difficult to bootstrap.

The goal is to modify `migrations/env.py` so that it reads the `APP_SETTINGS_MODULE` environment variable, dynamically imports the matching configuration module (e.g., `config.local`, `config.dev`, `config.staging`, `config.prod`), and extracts `SQLALCHEMY_DATABASE_URI` from it. The existing Flask-Migrate / `current_app` path should remain as a fallback so that the normal `flask db` workflow is not broken.

### Key Requirements

- Read `APP_SETTINGS_MODULE` environment variable at migration startup
- Dynamically import the configuration module indicated by `APP_SETTINGS_MODULE`
- Extract `SQLALCHEMY_DATABASE_URI` from the imported module
- Fall back to the existing Flask `current_app` / Flask-Migrate path if `APP_SETTINGS_MODULE` is not set
- Log which environment and database URL (masked) is being used
- No manual changes to migration scripts when switching environments
- Compatible with `flask db upgrade`, `flask db migrate`, and standalone `alembic upgrade head`
- Works in local, dev, staging, and production environments

### Affected Components

- `migrations/env.py` — core change: dynamic DB URL resolution
- `README.md` — updated migration instructions per environment
- `DOCUMENTATION/PROJECT.md` — changelog entry

## Priority

**High**

## Estimated Cost

**2 Story Points** (~1 day)

## Related Tasks

- [task_018_1.md](../TASKS/task_018_1.md) — Modify `migrations/env.py` for environment-aware DB URL resolution
- [task_018_2.md](../TASKS/task_018_2.md) — Test migration scripts in local and dev environments
- [task_018_3.md](../TASKS/task_018_3.md) — Update README.md with per-environment migration instructions
- [task_018_4.md](../TASKS/task_018_4.md) — Update DOCUMENTATION/PROJECT.md changelog

## Status

**0%**

## Trello

[US-018 — Environment-Aware Database Migrations](https://trello.com/c/1Hneaa4s)
```
