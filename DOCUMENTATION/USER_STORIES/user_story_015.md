# US-015 — Migrate to Async Framework or Add Async Support

## Title

Evaluate and Implement Async Support for I/O-Bound Operations

## User Story

As a **backend developer**, I want external API calls (password scoring) and email sending to be handled asynchronously, so that request latency is reduced and throughput is improved.

## Description

This can be achieved by introducing Celery with Redis as a message broker for background tasks (email sending, external API calls), or by evaluating a migration to Quart (async Flask) for native async/await support.

### Key Requirements

- Evaluate two approaches:
  1. **Celery + Redis**: background task queue for email sending and external API calls
  2. **Quart migration**: async/await native support (larger effort, higher reward)
- Recommended approach: **Celery + Redis** (lower risk, incremental adoption)
- Background tasks for:
  - Activation email sending (currently blocking the signup request)
  - Password reset email sending
  - External password scoring API calls (with circuit breaker)
  - Account deletion notification emails
- Celery worker configuration: separate process, auto-scaling
- Task retry and dead-letter queue support
- Task status monitoring (Flower dashboard or similar)
- Redis also reusable for rate limiting (US-001) and caching

### Affected Components

- `pyproject.toml` / `requirements.txt` (add `celery`, `redis`)
- New `worker/` directory for Celery configuration and task definitions
- `core/users/routes/signup.py` (offload email sending)
- `core/users/routes/email_activation.py` (offload email sending)
- `server/config/mails.py` (make email sending a Celery task)
- Docker Compose files (add Redis and Celery worker services)
- `config/default.py` (Celery broker settings)

## Priority

**Low**

## Estimated Cost

**8 Story Points** (~4 days)

## Related Tasks

- [task_015_1.md](../TASKS/task_015_1.md) — Set up Celery and Redis infrastructure
- [task_015_2.md](../TASKS/task_015_2.md) — Create Celery task for email sending
- [task_015_3.md](../TASKS/task_015_3.md) — Create Celery task for external API calls
- [task_015_4.md](../TASKS/task_015_4.md) — Update routes to use async tasks
- [task_015_5.md](../TASKS/task_015_5.md) — Add Redis and Celery worker to Docker Compose
- [task_015_6.md](../TASKS/task_015_6.md) — Configure task monitoring and error handling
- [task_015_7.md](../TASKS/task_015_7.md) — Write tests for async task execution

## Trello

[US-015 — Asynchronous Email Delivery](https://trello.com/c/US7pStaM)
