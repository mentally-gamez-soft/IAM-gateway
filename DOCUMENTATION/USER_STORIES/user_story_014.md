# US-014 — Two-Factor Authentication (2FA)

## Title

Add Optional TOTP-Based Two-Factor Authentication

## User Story

As a **security-conscious user**, I want to enable two-factor authentication on my account, so that my account is protected even if my password is compromised.

## Description

The implementation should use TOTP (Time-based One-Time Passwords) via `pyotp`. Users should be able to enable/disable 2FA from their profile, receive a QR code for authenticator apps, and provide a TOTP code during login. Backup recovery codes should be generated and stored securely.

### Key Requirements

- `POST /2fa/enable` — generates a TOTP secret, returns a QR code URI and backup recovery codes
- `POST /2fa/verify` — verifies a TOTP code to complete 2FA setup (prevents enabling without verification)
- `POST /2fa/disable` — disables 2FA for the user (requires current password + TOTP code)
- Login flow updated: after password verification, prompt for TOTP code if 2FA is enabled
- 8 backup recovery codes generated, hashed and stored in the database
- Each recovery code is single-use
- New fields on `GwUser`: `totp_secret` (encrypted), `two_factor_enabled`, `recovery_codes`
- QR code generation compatible with Google Authenticator, Authy, etc.
- TOTP window tolerance: 1 step (30 seconds before/after)

### Affected Components

- `pyproject.toml` / `requirements.txt` (add `pyotp`, `qrcode`)
- `core/users/models.py` (new 2FA fields)
- `core/users/routes/` (new `two_factor.py` module)
- `core/users/routes/login.py` (updated login flow for 2FA)
- `core/auth/` (2FA verification decorator)
- Database migration for new fields

## Priority

**Low**

## Estimated Cost

**8 Story Points** (~4 days)

## Related Tasks

- [task_014_1.md](../TASKS/task_014_1.md) — Add 2FA fields to GwUser model and create migration
- [task_014_2.md](../TASKS/task_014_2.md) — Implement 2FA enable endpoint with QR code generation
- [task_014_3.md](../TASKS/task_014_3.md) — Implement 2FA verification and disable endpoints
- [task_014_4.md](../TASKS/task_014_4.md) — Update login flow for 2FA challenge
- [task_014_5.md](../TASKS/task_014_5.md) — Implement backup recovery codes
- [task_014_6.md](../TASKS/task_014_6.md) — Write comprehensive tests for all 2FA flows
- [task_014_7.md](../TASKS/task_014_7.md) — Update Swagger documentation for 2FA endpoints

## Trello

[US-014 — Two-Factor Authentication (2FA)](https://trello.com/c/mIh1soOB)
