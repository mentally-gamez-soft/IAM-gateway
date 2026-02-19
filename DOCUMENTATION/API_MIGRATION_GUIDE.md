# API Migration Guide — Versioned API (US-006)

## Overview

All API endpoints are now available under the `/api/v1/` URL prefix.  
The legacy unversioned routes (e.g. `/login`) remain operational until the **sunset date** below, but every
response from those routes will include HTTP deprecation headers to signal that clients must migrate.

| | Old (deprecated) | New (current) |
|---|---|---|
| Base path | `/` | `/api/v1/` |
| Swagger `basePath` | `/Service-Name/api/v1.0.0a` | `/api/v1` |
| Sunset date | — | **2026-09-01** |

---

## Route Mapping

| Action | Deprecated URL | Current URL |
|---|---|---|
| Sign up | `POST /signup` | `POST /api/v1/signup` |
| Log in | `POST /login` | `POST /api/v1/login` |
| Log out | `POST /logout` | `POST /api/v1/logout` |
| Confirm account | `GET /confirm/<token>` | `GET /api/v1/confirm/<token>` |
| Resend confirmation | `POST /resend-confirmation` | `POST /api/v1/resend-confirmation` |
| Add role | `POST /role/add` | `POST /api/v1/role/add` |
| Forgot password | `POST /forgot-password` | `POST /api/v1/forgot-password` |
| Reset password | `POST /reset-password/<token>` | `POST /api/v1/reset-password/<token>` |
| Refresh token | `POST /token/refresh` | `POST /api/v1/token/refresh` |
| Health probe | `GET /health` | `GET /health` _(no change)_ |
| Readiness probe | `GET /ready` | `GET /ready` _(no change)_ |

> **Note**: Health and readiness probes remain at the root level and are intentionally not versioned.

---

## Deprecation HTTP Headers

Every response from a legacy (unversioned) route will include the following headers:

```http
Deprecation: true
Sunset: 2026-09-01
Link: </api/v1/<route>>; rel="successor-version"
```

### Example

**Request:**
```http
POST /login HTTP/1.1
Content-Type: application/json

{"email": "user@example.com", "password": "..."}
```

**Response headers (deprecated route):**
```http
HTTP/1.1 200 OK
Deprecation: true
Sunset: 2026-09-01
Link: </api/v1/login>; rel="successor-version"
Content-Type: application/json
```

Requests to `/api/v1/login` (the versioned route) do **not** carry these headers.

---

## Breaking Change: Token Response Key Rename

The login response payload key was renamed from `jwt` to `access_token`:

**Before (deprecated):**
```json
{
  "data": {
    "user": "<base64-encoded-user-id>",
    "jwt": "<access-token>"
  }
}
```

**After (current):**
```json
{
  "data": {
    "user": "<base64-encoded-user-id>",
    "access_token": "<access-token>",
    "refresh_token": "<refresh-token>",
    "token_type": "Bearer",
    "expires_in": 900
  }
}
```

Any client sending the token back to protected endpoints must now use the `access_token` key inside the `data` object:

```json
{
  "data": {
    "user": "<base64-encoded-user-id>",
    "access_token": "<access-token>"
  }
}
```

---

## Migration Steps for API Consumers

1. **Update all endpoint URLs** — append `/api/v1` prefix to all API calls (except `/health` and `/ready`).
2. **Update token key** — rename `data.jwt` → `data.access_token` throughout your codebase.
3. **Store the refresh token** — persist `data.refresh_token` from the login response; use `POST /api/v1/token/refresh` to obtain a new access token when it expires.
4. **Monitor deprecation headers** — if any response contains `Deprecation: true`, the URL must be updated immediately.
5. **Complete migration before sunset** — legacy routes will be removed on **2026-09-01**.

---

## Timeline

| Date | Event |
|---|---|
| 2026-02-01 (approx.) | US-006 released — `/api/v1/` routes available; legacy routes emit deprecation headers |
| **2026-09-01** | Sunset date — legacy routes removed |

---

## Questions?

Open an issue or contact the backend team.
