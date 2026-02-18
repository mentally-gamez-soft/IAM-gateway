# US-003 — Refresh Token Mechanism

## Title

Implement JWT Refresh Token for Session Continuity

## User Story

As a **user**, I want my session to remain active without re-entering credentials frequently, so that I have a seamless experience.

## Description

Currently, the JWT has a single expiration with no refresh mechanism. A short-lived access token (15 min) paired with a long-lived refresh token (7 days) should be issued. A `/token/refresh` endpoint should accept a valid refresh token and return a new access token. Refresh tokens must be stored securely in the database with rotation and revocation support.

### Key Requirements

- Dual token system: short-lived access token (15 min) + long-lived refresh token (7 days)
- `POST /token/refresh` endpoint accepting a refresh token and returning a new access token
- Refresh token rotation: each refresh invalidates the old token and issues a new one
- Refresh token stored in `GwUser` model (or a dedicated `RefreshToken` table)
- Token family tracking to detect refresh token reuse (indicating theft)
- Revocation of all refresh tokens on logout or password change
- Configurable token lifetimes per environment

### Affected Components

- `core/auth/jwt/jwt_handler.py` (access/refresh token generation)
- `core/users/models.py` (new `RefreshToken` model or fields)
- `core/users/routes/` (new `token.py` module)
- `core/users/routes/login.py` (issue both tokens)
- `core/users/routes/logout.py` (revoke refresh token)
- `config/default.py` (new token lifetime settings)
- Database migration

## Priority

**High**

## Estimated Cost

**5 Story Points** (~2.5 days)

## Related Tasks

- [task_003_1.md](../TASKS/task_003_1.md) — Design and create RefreshToken model
- [task_003_2.md](../TASKS/task_003_2.md) — Update JWT handler for dual-token generation
- [task_003_3.md](../TASKS/task_003_3.md) — Implement token refresh endpoint
- [task_003_4.md](../TASKS/task_003_4.md) — Update login/logout routes for dual-token flow
- [task_003_5.md](../TASKS/task_003_5.md) — Add token family tracking and reuse detection
- [task_003_6.md](../TASKS/task_003_6.md) — Write tests for refresh token lifecycle

## Trello

[US-003 — JWT Refresh Token Mechanism](https://trello.com/c/TQcTaOnP)
