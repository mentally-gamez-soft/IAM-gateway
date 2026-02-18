# US-004 — Structured JSON Logging

## Title

Replace Text Logging with Structured JSON Logs

## User Story

As a **DevOps engineer**, I want the application to output logs in structured JSON format, so that logs can be easily parsed, searched, and aggregated by centralized log management tools (ELK, Loki, Datadog).

## Description

Each log entry should include: timestamp, log level, logger name, function, line number, request ID, user ID (if authenticated), and the message. The `python-json-logger` library should be used. Console output should remain human-readable in local/dev environments.

### Key Requirements

- JSON-formatted log output for staging and production environments
- Human-readable text format retained for local and development environments
- Standard fields per log entry: `timestamp`, `level`, `logger`, `function`, `lineno`, `request_id`, `user_id`, `message`
- Integration with Flask request context to extract `request_id` and `user_id`
- File handler and console handler both supporting the new format
- Email handler (SMTP) format updated accordingly
- Backward-compatible: no breaking changes to existing log consumers

### Affected Components

- `server/config/logs.py` (main changes)
- `config/default.py` (log format settings)
- `pyproject.toml` / `requirements.txt` (new dependency: `python-json-logger`)

## Priority

**High**

## Estimated Cost

**3 Story Points** (~1.5 days)

## Related Tasks

- [task_004_1.md](../TASKS/task_004_1.md) — Add python-json-logger dependency
- [task_004_2.md](../TASKS/task_004_2.md) — Implement JSON log formatter
- [task_004_3.md](../TASKS/task_004_3.md) — Add request context fields to log records
- [task_004_4.md](../TASKS/task_004_4.md) — Configure environment-specific log formats
- [task_004_5.md](../TASKS/task_004_5.md) — Write tests for logging configuration

## Trello

[US-004 — Structured JSON Logging](https://trello.com/c/FbsQV8hE)
