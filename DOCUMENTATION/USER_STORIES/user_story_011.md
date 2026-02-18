# US-011 — User Profile Management

## Title

Add User Profile Viewing and Editing

## User Story

As a **user**, I want to view and update my profile information (username, email), so that I can manage my account details.

## Description

A `GET /profile` endpoint should return the authenticated user's information, and a `PUT /profile` endpoint should allow updating username and email (with re-validation and uniqueness checks). Email changes should trigger a new activation flow.

### Key Requirements

- `GET /profile` — returns the authenticated user's data: `id`, `username`, `email`, `roles`, `created_on`, `active`, `activated_on`
- `PUT /profile` — accepts `{"username": "...", "email": "..."}` to update profile fields
- Username change: validate uniqueness and formatting rules
- Email change: validate format & uniqueness, set `active=False`, trigger new activation email
- Both endpoints require authentication (`authorization_guard`, `login_required`)
- Prevent updating to an already-taken username or email
- Response includes updated user data and fresh JWT (if roles/email changed)

### Affected Components

- `core/users/routes/` (new `profile.py` module)
- `core/users/models.py` (potential new methods)
- `core/users/__init__.py` (register new blueprint routes)
- `core/auth/middlewares/validation_token.py` (reuse activation token logic)
- `server/config/mails.py` (reuse activation email)
- Swagger documentation

## Priority

**Medium**

## Estimated Cost

**3 Story Points** (~1.5 days)

## Related Tasks

- [task_011_1.md](../TASKS/task_011_1.md) — Implement GET /profile endpoint
- [task_011_2.md](../TASKS/task_011_2.md) — Implement PUT /profile endpoint with validation
- [task_011_3.md](../TASKS/task_011_3.md) — Handle email change re-activation flow
- [task_011_4.md](../TASKS/task_011_4.md) — Write tests for profile endpoints
- [task_011_5.md](../TASKS/task_011_5.md) — Update Swagger documentation

## Trello

[US-011 — User Profile Management](https://trello.com/c/HgKsACIf)
