# US-012 — Account Deletion (GDPR Compliance)

## Title

Implement User Account Soft Delete and Data Export

## User Story

As a **user**, I want to be able to delete my account and export my data, so that my rights under GDPR/data protection regulations are respected.

## Description

A `DELETE /account` endpoint should soft-delete the user (already partially supported via `deleted` flag and `deactivated_on`). A `GET /account/export` endpoint should return all user data in JSON format. A scheduled job should permanently purge soft-deleted accounts after a retention period (e.g., 30 days).

### Key Requirements

- `DELETE /account` — soft-deletes the user: sets `deleted=True`, `deactivated_on=now()`, revokes JWT, logs out user
- `GET /account/export` — returns all user data in JSON format (user info, roles, activity stats)
- Consent confirmation required for deletion (e.g., `{"confirm": true}` in request body)
- Scheduled purge job: permanently remove soft-deleted accounts after 30-day retention
- Purge job removes all related data (roles, stats, tokens)
- Audit trail: log all deletion and export requests
- Email notification sent upon account deletion confirmation

### Affected Components

- `core/users/routes/` (new `account.py` module)
- `core/users/models.py` (purge methods, data export methods)
- New scheduled task / CLI command for purge job
- `server/config/mails.py` (deletion confirmation email)
- Database migration (if schema changes needed)

## Priority

**Medium**

## Estimated Cost

**5 Story Points** (~2.5 days)

## Related Tasks

- [task_012_1.md](../TASKS/task_012_1.md) — Implement DELETE /account soft-delete endpoint
- [task_012_2.md](../TASKS/task_012_2.md) — Implement GET /account/export data export endpoint
- [task_012_3.md](../TASKS/task_012_3.md) — Create scheduled purge job for expired soft-deleted accounts
- [task_012_4.md](../TASKS/task_012_4.md) — Add deletion confirmation email notification
- [task_012_5.md](../TASKS/task_012_5.md) — Write tests for account deletion and export flows
- [task_012_6.md](../TASKS/task_012_6.md) — Document GDPR compliance procedures

## Trello

[US-012 — Account Deletion (GDPR Compliance)](https://trello.com/c/H0oL6538)
