# US-008 — Dockerize with Non-Root User

## Title

Run Docker Containers as Non-Root User

## User Story

As a **security engineer**, I want the application Docker container to run as a non-root user, so that any container escape vulnerability has limited impact.

## Description

The Dockerfile should create a dedicated `appuser` with minimal permissions, own the `/app` directory, and execute Gunicorn under this user. The Nginx container should also be configured to run as non-root.

### Key Requirements

- Create a dedicated non-root user `appuser` (UID 1000) in the Dockerfile
- Transfer ownership of `/app` directory to `appuser`
- Use `USER appuser` directive before the `CMD`/`ENTRYPOINT`
- Nginx container configured with a non-root user and writable temp/log directories
- Verify that all file paths (logs, uploads, static) remain writable by the non-root user
- No changes to application logic — only Docker configuration

### Affected Components

- `Dockerfile` (add user creation and switch)
- `Docker/nginx/prod/Dockerfile` (non-root Nginx config)
- `Docker/nginx/prod/nginx.conf` (adjust pid/temp paths for non-root)
- `Docker/application/dev/docker-compose-dev.yaml` (optional: user directive)
- `Docker/application/prod/docker-compose-prod.yaml` (optional: user directive)

## Priority

**High**

## Estimated Cost

**1 Story Point** (~0.5 day)

## Related Tasks

- [task_008_1.md](../TASKS/task_008_1.md) — Update application Dockerfile for non-root execution
- [task_008_2.md](../TASKS/task_008_2.md) — Update Nginx Dockerfile and config for non-root execution
- [task_008_3.md](../TASKS/task_008_3.md) — Validate permissions on logs and upload directories
- [task_008_4.md](../TASKS/task_008_4.md) — Test container startup and functionality as non-root

## Trello

[US-008 — Dockerize with Non-Root User](https://trello.com/c/8xZQ5wiw)
