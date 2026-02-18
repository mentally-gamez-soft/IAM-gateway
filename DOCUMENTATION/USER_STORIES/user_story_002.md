# US-002 — Password Reset / Forgot Password Flow

## Title

Add Password Reset Functionality via Email

## User Story

As a **user**, I want to be able to reset my password if I forget it, so that I can regain access to my account.

## Description

The system should expose a `/forgot-password` endpoint that accepts an email, generates a time-limited reset token (using `itsdangerous`), sends a reset link via email, and provides a `/reset-password/<token>` endpoint to set a new password. The old password should be invalidated, the JWT session revoked, and the user required to log in again.

### Key Requirements

- `POST /forgot-password` endpoint accepting `{"email": "..."}` — always returns 200 (prevent email enumeration)
- Time-limited reset token generated via `itsdangerous.URLSafeTimedSerializer` (configurable expiration, default 30 minutes)
- Email sent with a reset link containing the token
- `POST /reset-password/<token>` endpoint accepting `{"password": "..."}` — validates the token, applies password rules, updates the hash
- Invalidate all existing JWT sessions upon password reset
- Store `last_password_reset_token` in the `GwUser` model to prevent token reuse
- Rate-limit the forgot-password endpoint to prevent abuse

### Affected Components

- `core/users/routes/` (new `password_reset.py` module)
- `core/users/models.py` (new field `last_password_reset_token`)
- `core/auth/middlewares/validation_token.py` (reuse token generation logic)
- `server/config/mails.py` (password reset email template)
- `config/default.py` (reset token expiration setting)
- Database migration for new field

## Priority

**Critical**

## Estimated Cost

**5 Story Points** (~2.5 days)

## Related Tasks

- [task_002_1.md](../TASKS/task_002_1.md) — Add password reset token field to GwUser model
- [task_002_2.md](../TASKS/task_002_2.md) — Implement forgot-password endpoint
- [task_002_3.md](../TASKS/task_002_3.md) — Implement reset-password endpoint
- [task_002_4.md](../TASKS/task_002_4.md) — Create password reset email template and sending logic
- [task_002_5.md](../TASKS/task_002_5.md) — Write tests for the password reset flow
- [task_002_6.md](../TASKS/task_002_6.md) — Update Swagger documentation

## Trello

[US-002 — Password Reset / Forgot Password Flow](https://trello.com/c/Z4vE1PQM)
