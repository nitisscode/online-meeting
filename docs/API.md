# API Reference

Base URL (local): `http://127.0.0.1:8000`

All request and response bodies are JSON. Send `Content-Type: application/json`.

Real-time chat over WebSocket is documented separately in [WEBSOCKET_CHAT.md](WEBSOCKET_CHAT.md).

## Authentication

Protected endpoints require a JWT access token:

```
Authorization: Bearer <access_token>
```

| Token | Lifetime | Notes |
|-------|----------|-------|
| Access | 30 minutes (`JWT_ACCESS_TOKEN_LIFETIME_MINUTES`) | Sent on every protected request |
| Refresh | 7 days (`JWT_REFRESH_TOKEN_LIFETIME_DAYS`) | Rotated on refresh; old one is blacklisted |

Access tokens carry `user_id`, `email` and `username` claims.

## Error format

| Status | When | Body |
|--------|------|------|
| 400 | Field validation failed | `{"field_name": ["message"]}` |
| 400 | Business rule failed | `{"detail": "message"}` |
| 401 | Missing, invalid or expired token | `{"detail": "Authentication credentials were not provided."}` |
| 403 | Not allowed (e.g. wrong pass code) | `{"detail": "message"}` |
| 404 | Not found, or not visible to you | `{"detail": "Not found."}` |

Every error except field validation uses a single `detail` key with a string message.

## Enums

All enums are sent and returned as integers.

**OTP purpose**

| Value | Meaning |
|-------|---------|
| 0 | Login |
| 1 | Email verification |
| 2 | Password reset |

**Meeting status**

| Value | Meaning |
|-------|---------|
| 0 | Scheduled |
| 1 | Live |
| 2 | Ended |
| 3 | Cancelled |

**Participant role**

| Value | Meaning |
|-------|---------|
| 0 | Host |
| 1 | Co-host |
| 2 | Participant |

**Connection status**

| Value | Meaning |
|-------|---------|
| 0 | Connecting |
| 1 | Connected |
| 2 | Disconnected |
| 3 | Left |
| 4 | Invited |

---

# Users

## Sign up

`POST /users/signup/` — public

**Body**

```json
{
  "username": "nitish",
  "email": "nitish@example.com",
  "first_name": "Nitish",
  "last_name": "Kumar",
  "password": "StrongPass123!",
  "confirm_password": "StrongPass123!"
}
```

| Field | Required |
|-------|----------|
| `username` | yes |
| `email` | yes |
| `first_name` | yes |
| `last_name` | no |
| `password` | yes |
| `confirm_password` | yes, must match `password` |

**201 Created**

```json
{
  "username": "nitish",
  "email": "nitish@example.com",
  "first_name": "Nitish",
  "last_name": "Kumar"
}
```

**Errors (400):** `{"email": ["Email already exists."]}`, `{"username": ["Username already exists."]}`, `{"confirm_password": ["Passwords do not match."]}`

## Log in (password)

`POST /users/login/` — public

The `email` field accepts either the email or the username.

**Body**

```json
{
  "email": "nitish@example.com",
  "password": "StrongPass123!"
}
```

**200 OK**

```json
{
  "refresh": "<refresh_token>",
  "access": "<access_token>"
}
```

**Errors (401):** `No active user found with this email or username.`, `Incorrect email or password.`, `Your account is inactive. Contact support.`

## Request OTP

`POST /users/otp/request/` — public

Creates a 4-digit OTP, valid for 2 minutes (`OTP_EXPIRY_SECONDS`), and emails it to the user.

**Body**

```json
{
  "email": "nitish@example.com",
  "purpose": 0
}
```

**201 Created**

```json
{
  "email": "nitish@example.com",
  "purpose": 0,
  "otp": "4821"
}
```

> `otp` is returned for development only. Remove it before production.

**Errors (400):** `{"detail": "User not found"}`, `{"detail": "Failed to send OTP"}`

## Verify OTP (log in)

`POST /users/otp/verify/` — public

Only `purpose: 0` (login) issues tokens.

**Body**

```json
{
  "email": "nitish@example.com",
  "purpose": 0,
  "otp": "4821"
}
```

**200 OK**

```json
{
  "refresh": "<refresh_token>",
  "access": "<access_token>",
  "user": {
    "id": "c54451c6-ebee-48a6-903d-f5c51fafbf78",
    "username": "nitish",
    "email": "nitish@example.com",
    "first_name": "Nitish",
    "last_name": "Kumar"
  }
}
```

**Errors (400):** `{"detail": "Invalid Request"}` (purpose is not login), `{"detail": "Invalid OTP"}`, `{"detail": "OTP expired"}`, `{"detail": "User not found"}`

## Refresh token

`POST /users/token/refresh/` — public

**Body**

```json
{ "refresh": "<refresh_token>" }
```

**200 OK** — a new refresh token is returned and the old one is blacklisted.

```json
{
  "access": "<new_access_token>",
  "refresh": "<new_refresh_token>"
}
```

**Errors (401):** `{"detail": "Token is blacklisted", "code": "token_not_valid"}` and other invalid-token messages.

## Log out (blacklist refresh token)

`POST /users/token/blacklist/` — public

**Body**

```json
{ "refresh": "<refresh_token>" }
```

**200 OK** — `{}`

## Current user

`GET /users/me/` — authenticated

**200 OK**

```json
{
  "id": "c54451c6-ebee-48a6-903d-f5c51fafbf78",
  "username": "nitish",
  "email": "nitish@example.com",
  "first_name": "Nitish",
  "last_name": "Kumar"
}
```

---

# Meetings

All meeting endpoints require authentication. List, retrieve, update and delete only return meetings **you created**; other meetings return 404.

## List my meetings

`GET /meetings/`

**200 OK** — not paginated.

```json
[
  {
    "id": "0fa29bfc-14d9-4304-992e-dc9f378347f5",
    "title": "Team Standup",
    "status": 0,
    "scheduled_at": "2026-10-13T10:00:00Z",
    "started_at": null,
    "ended_at": null,
    "meeting_code": "2CN76P879R"
  }
]
```

## Create meeting

`POST /meetings/`

Creates the meeting, its settings, and adds you as the host participant in one transaction.

**Body**

```json
{
  "title": "Team Standup",
  "description": "Daily sync",
  "scheduled_at": "2026-10-13T10:00:00Z",
  "is_private": true,
  "pass_code": "1234",
  "settings": {
    "allow_chat": true,
    "allow_screen_share": true,
    "allow_recording": false,
    "waiting_room_enabled": true,
    "allow_raise_hand": true
  }
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `title` | yes | max 255 chars |
| `description` | no | |
| `scheduled_at` | no | ISO 8601 datetime |
| `is_private` | no | default `false` |
| `pass_code` | no | max 10 chars; required to join if set |
| `settings` | no | any omitted setting uses its default |
| `status`, `started_at`, `ended_at` | no | accepted, but use the start/end endpoints instead |

**Settings defaults:** `allow_chat: true`, `allow_screen_share: true`, `allow_recording: false`, `waiting_room_enabled: false`, `allow_raise_hand: true`

**201 Created**

```json
{
  "id": "0fa29bfc-14d9-4304-992e-dc9f378347f5",
  "title": "Team Standup",
  "description": "Daily sync",
  "meeting_code": "2CN76P879R",
  "status": 0,
  "scheduled_at": "2026-10-13T10:00:00Z",
  "started_at": null,
  "ended_at": null,
  "is_private": true,
  "pass_code": "1234",
  "created_by": "c54451c6-ebee-48a6-903d-f5c51fafbf78",
  "settings": {
    "id": "2bbf169c-e51b-4774-96ee-3cb323951257",
    "meeting": "0fa29bfc-14d9-4304-992e-dc9f378347f5",
    "allow_chat": true,
    "allow_screen_share": true,
    "allow_recording": false,
    "waiting_room_enabled": true,
    "allow_raise_hand": true
  }
}
```

## Get meeting

`GET /meetings/{meeting_id}/`

**200 OK** — same shape as the create response.

## Update meeting settings

`PATCH /meetings/{meeting_id}/` or `PUT /meetings/{meeting_id}/`

Only `settings` can be changed; all other meeting fields are read-only here.

**Body**

```json
{
  "settings": {
    "allow_chat": false
  }
}
```

**200 OK** — same shape as the create response.

## Delete meeting

`DELETE /meetings/{meeting_id}/`

**204 No Content**

## Start meeting

`POST /meetings/{meeting_id}/start/`

No body. Sets status to Live (`1`) and records `started_at`.

**200 OK** — `{"detail": "Meeting started."}`

**Errors (400):** `{"detail": "Meeting has ended"}`, `{"detail": "Meeting has been cancelled"}`, `{"detail": "Meeting is already ongoing"}`

## End meeting

`POST /meetings/{meeting_id}/end/`

No body. Sets status to Ended (`2`) and records `ended_at`.

**200 OK** — `{"detail": "Meeting ended."}`

**Errors (400):** `{"detail": "Meeting is not ongoing"}`

## Join meeting

`POST /meetings/join/`

Joins a Live meeting by its code. Any authenticated user can join, not only the creator. Joining again updates the existing participant row (no duplicate) and resets `joined_at`.

**Body**

```json
{
  "meeting_code": "2CN76P879R",
  "pass_code": "1234"
}
```

| Field | Required | Notes |
|-------|----------|-------|
| `meeting_code` | yes | |
| `pass_code` | only if the meeting has one | must match exactly |

**200 OK** — the meeting room, same shape as [Meeting room](#meeting-room-participants). You are now listed as a connected participant.

**Errors:**

| Status | Body | When |
|--------|------|------|
| 400 | `{"meeting_code": ["This field is required."]}` | `meeting_code` missing |
| 404 | `{"detail": "Invalid meeting code."}` | No meeting with this code |
| 400 | `{"detail": "Meeting is not ongoing"}` | Meeting is Scheduled (not started) |
| 400 | `{"detail": "Meeting has ended"}` | Meeting is Ended |
| 400 | `{"detail": "Meeting has been cancelled"}` | Meeting is Cancelled |
| 403 | `{"detail": "Invalid pass code."}` | `pass_code` missing or wrong |

## Meeting room (participants)

`GET /meetings/{meeting_id}/participants/`

Visible to the meeting creator and to users currently connected to the meeting. Lists only **connected** participants, host first.

**200 OK**

```json
{
  "id": "0fa29bfc-14d9-4304-992e-dc9f378347f5",
  "title": "Team Standup",
  "meeting_code": "2CN76P879R",
  "status": 1,
  "settings": {
    "id": "2bbf169c-e51b-4774-96ee-3cb323951257",
    "meeting": "0fa29bfc-14d9-4304-992e-dc9f378347f5",
    "allow_chat": true,
    "allow_screen_share": true,
    "allow_recording": false,
    "waiting_room_enabled": false,
    "allow_raise_hand": true
  },
  "participants": [
    {
      "id": "123dfb06-f1d3-4837-a5c5-928a57354e66",
      "user": {
        "id": "c54451c6-ebee-48a6-903d-f5c51fafbf78",
        "username": "nitish",
        "email": "nitish@example.com",
        "first_name": "Nitish",
        "last_name": "Kumar"
      },
      "role": 0,
      "connection_status": 1,
      "joined_at": "2026-10-13T10:01:12Z",
      "left_at": null
    }
  ]
}
```

---

# Known issues

These were found while verifying this document against the code.

| Endpoint | Issue |
|----------|-------|
| `/meetings/participants/` | Unreachable: the URL resolves to the meeting detail route with `participants` as the meeting ID. Use `GET /meetings/{meeting_id}/participants/` instead. |
| `POST /meetings/{id}/start/` and `/end/` | Any authenticated user can start or end any meeting; the lookup does not check the creator. |
| `PATCH` / `PUT /meetings/{id}/` | Returns 500 when the body has no `settings`, because `update()` returns nothing in that case. |
| `GET /meetings/{id}/participants/` | The host is created without a connection status, so the host is not listed until they call `POST /meetings/join/`. |
| `POST /users/otp/request/` | Returns the OTP in the response. |
