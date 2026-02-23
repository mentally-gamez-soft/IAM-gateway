```markdown
# US-019 — Test Coverage Measurement

## Title

Integrate `coverage` Library to Measure and Report Test Coverage

## User Story

As a **developer**, I want to measure the test coverage of the IAM Gateway project using the `coverage` library, so that I can identify untested code paths, assess the quality of the test suite, and make informed decisions about where to add new tests.

## Description

The project has a comprehensive test suite using `unittest`, but there is currently no way to measure how much of the application code is exercised by the tests. Integrating the `coverage` library will allow developers to run all tests and produce coverage reports (console summary, HTML) that highlight which lines and branches are not covered.

### Key Requirements

- Add `coverage` as a project dependency (in `requirements.in`, `requirements.txt`, and `pyproject.toml`)
- Create a `.coveragerc` configuration file at the project root to:
  - Set the source to the application packages (`core`, `config`, `server`)
  - Exclude non-application code (tests, migrations, venv, config stubs)
  - Enable branch coverage measurement
  - Configure HTML report output directory (`htmlcov/`)
- Document how to run the tests with coverage in `README.md` and `DOCUMENTATION/PROJECT.md`
- The HTML coverage report directory (`htmlcov/`) must be added to `.gitignore`
- Running `coverage run` must be equivalent to running the existing test suite commands (no test behaviour changes)

### Affected Components

- `requirements.in` — add `coverage` dependency
- `requirements.txt` — add `coverage` dependency
- `pyproject.toml` — add `coverage` dependency and optional tool config
- `.coveragerc` — new file: coverage configuration
- `.gitignore` — add `htmlcov/` and `.coverage`
- `README.md` — coverage instructions section
- `DOCUMENTATION/PROJECT.md` — coverage instructions section

## Priority

**Medium**

## Estimated Cost

**1 Story Point** (~half a day)

## Related Tasks

- [task_019_1.md](../TASKS/task_019_1.md) — Add `coverage` to project dependencies
- [task_019_2.md](../TASKS/task_019_2.md) — Create `.coveragerc` configuration file
- [task_019_3.md](../TASKS/task_019_3.md) — Update `.gitignore` for coverage artefacts
- [task_019_4.md](../TASKS/task_019_4.md) — Update `README.md` and `DOCUMENTATION/PROJECT.md`

## Status

**0%**

## Trello

[US-019 — Test Coverage Measurement](https://trello.com/c/OPldO6DP)
```
