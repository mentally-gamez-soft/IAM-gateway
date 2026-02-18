# US-017 — Add Integration Tests with Testcontainers

## Title

Create Integration Test Suite with Real PostgreSQL via Testcontainers

## User Story

As a **developer**, I want integration tests that run against a real PostgreSQL instance, so that database-specific behaviors (constraints, migrations, transactions) are validated before deployment.

## Description

Use `testcontainers-python` to spin up a PostgreSQL container during test execution. The CI pipeline should run these tests in a separate stage after unit tests.

### Key Requirements

- Install and configure `testcontainers-python` with PostgreSQL module
- Integration test base class that:
  - Spins up a PostgreSQL container before test suite
  - Runs Alembic migrations (`flask db upgrade`) against the container
  - Seeds test data
  - Tears down the container after all tests
- Test coverage for:
  - User creation with all database constraints (unique username, unique email)
  - Role assignment with foreign key integrity
  - Account activation workflow with database state changes
  - Concurrent user operations (transaction isolation)
  - Migration up/down cycle validation
- Separate test configuration (`config/testing_integration.py`)
- CI pipeline stage: `integration-tests` (runs after unit tests, requires Docker)
- Tests tagged/grouped separately from unit tests for selective execution

### Affected Components

- `pyproject.toml` / `requirements.txt` (add `testcontainers`)
- `tests/` (new `test_integration/` subdirectory)
- `config/` (new `testing_integration.py`)
- `.github/workflows/ci.yml` (new CI stage)
- `tests/__init__.py` (updated base test class)

## Priority

**Medium**

## Estimated Cost

**5 Story Points** (~2.5 days)

## Related Tasks

- [task_017_1.md](../TASKS/task_017_1.md) — Set up testcontainers infrastructure and base class
- [task_017_2.md](../TASKS/task_017_2.md) — Create integration test configuration
- [task_017_3.md](../TASKS/task_017_3.md) — Write integration tests for user lifecycle
- [task_017_4.md](../TASKS/task_017_4.md) — Write integration tests for database constraints
- [task_017_5.md](../TASKS/task_017_5.md) — Add migration cycle validation tests
- [task_017_6.md](../TASKS/task_017_6.md) — Configure CI pipeline for integration test stage

## Trello

[US-017 — Integration and End-to-End Test Suite](https://trello.com/c/JkbcZVgm)
