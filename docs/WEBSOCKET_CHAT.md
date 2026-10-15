# WebSocket Chat

Real-time chat for a meeting. Every meeting has one conversation; members of that conversation can send, edit and delete messages and see typing indicators live.

- Transport: WebSocket, JSON text frames only.
- Auth: JWT access token in the URL query string.
- History: loaded over REST (see [Loading history](#loading-history)); the socket only carries live events.

---

## 1. Connecting

```
ws://127.0.0.1:8000/ws/chat/<conversation_id>/?token=<access_token>
```

Use `wss://` in production.

| Part | Value |
|------|-------|
| `conversation_id` | UUID of the meeting's conversation. Must be a valid UUID, otherwise the handshake fails. |
| `token` | The `access` token from `POST /users/login/` or `POST /users/otp/verify/`. Not the refresh token. |

Browsers cannot set an `Authorization` header on a WebSocket, which is why the token goes in the query string.

### Who can connect

You must be a member of the conversation. Calling `POST /meetings/join/` (see [API.md](API.md#join-meeting)) adds you as a member. The meeting host must also call join; creating a meeting does not add the host to the chat.

### Connection lifecycle

The server always accepts the handshake first, then closes immediately if a check fails. Read the close `code` and `reason` in your `onclose` handler.

| Close code | `reason` | When | What the client should do |
|-----------|----------|------|---------------------------|
| `4001` | `Unauthorized` | Token missing, invalid, expired at connect time, or user inactive | Refresh the access token and reconnect; if that fails, log in again |
| `4003` | `You are not a member of this conversation` | User is not a member | Do not retry; call `POST /meetings/join/` first |
| `4003` | `Token expired` | The access token expired while connected | Refresh the access token (`POST /users/token/refresh/`) and reconnect |

`4003` is used for two different cases. Tell them apart by `reason`.

The server closes the socket at the exact moment the access token expires (default lifetime: 60 minutes, `JWT_ACCESS_TOKEN_LIFETIME_MINUTES`).

---

## 2. Frame format

Every frame, in both directions, is one JSON object:

```json
{ "op": <integer>, "data": { ... } }
```

- `op`: which operation or event this is (see [Constants](#5-constants)).
- `data`: the payload for that operation.

---

## 3. Client → server operations

### Send a message: `op: 1`

```json
{ "op": 1, "data": { "content": "Hello everyone", "content_type": 1 } }
```

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| `content` | string | yes | 1–1000 characters |
| `content_type` | integer | yes | One of [ContentType](#content-type) |

The server saves the message and sends [`op: 0`](#new-message-op-0) to **every other member**. The sender does **not** receive it back (see [Known limitations](#7-known-limitations)).

### Edit a message: `op: 2`

```json
{ "op": 2, "data": { "message_id": "d4377b8c-4b68-4148-9626-4f168db4533c", "content": "Hello everyone (edited)", "content_type": 1 } }
```

| Field | Type | Required | Rules |
|-------|------|----------|-------|
| `message_id` | UUID string | yes | Must be a message in this conversation that is not deleted |
| `content` | string | yes | 1–1000 characters |
| `content_type` | integer | yes | One of [ContentType](#content-type) |

Only the sender of the message can edit it. On success, **every member including the editor** receives [`op: 2`](#message-edited-op-2).

### Delete a message: `op: 3`

```json
{ "op": 3, "data": { "message_id": "d4377b8c-4b68-4148-9626-4f168db4533c" } }
```

| Field | Type | Required |
|-------|------|----------|
| `message_id` | UUID string | yes |

Only the sender can delete. The message is soft-deleted (kept in the database with `is_deleted: true`). **Every member including the deleter** receives [`op: 3`](#message-deleted-op-3).

### Typing indicator: `op: 5`

```json
{ "op": 5, "data": { "is_typing": true } }
```

| Field | Type | Required |
|-------|------|----------|
| `is_typing` | boolean | yes |

**Every other member** receives [`op: 5`](#typing-op-5). The server does not time out typing state: send `is_typing: false` when the user stops typing (for example after 3 seconds without input) or sends the message.

---

## 4. Server → client events

### New message: `op: 0`

Sent to every member except the sender.

```json
{
  "op": 0,
  "data": {
    "id": "d4377b8c-4b68-4148-9626-4f168db4533c",
    "sender": {
      "id": "238336a2-bea1-4557-a9d1-96412cde8e19",
      "username": "nitiss",
      "email": "nitishkumar50805@gmail.com",
      "first_name": "Nitish",
      "last_name": "Kumar"
    },
    "created_at": "2026-10-15T16:12:08.825955+05:30",
    "modified_at": "2026-10-15T16:12:08.825955+05:30",
    "is_deleted": false,
    "content": "Hello everyone",
    "content_type": 1,
    "is_edited": false,
    "edited_at": null,
    "conversation": "b61cb035-8b4d-4256-aec7-3757c03274cb"
  }
}
```

#### Message object

| Field | Type | Notes |
|-------|------|-------|
| `id` | UUID string | Use this for edit and delete |
| `sender` | object | `id`, `username`, `email`, `first_name`, `last_name` |
| `created_at` | ISO 8601 string | |
| `modified_at` | ISO 8601 string | Not updated on edit; use `edited_at` |
| `is_deleted` | boolean | |
| `content` | string | |
| `content_type` | integer | [ContentType](#content-type) |
| `is_edited` | boolean | |
| `edited_at` | ISO 8601 string or `null` | |
| `conversation` | UUID string | |

### Message edited: `op: 2`

Sent to every member, including the editor. `data` is the full updated [message object](#message-object), with `is_edited: true` and `edited_at` set.

```json
{ "op": 2, "data": { "id": "d4377b8c-...", "content": "Hello everyone (edited)", "is_edited": true, "edited_at": "2026-10-15T16:20:41.102938+05:30", "...": "..." } }
```

### Message deleted: `op: 3`

Sent to every member, including the deleter. Remove the message from the UI, or show "message deleted".

```json
{ "op": 3, "data": { "message_id": "d4377b8c-4b68-4148-9626-4f168db4533c" } }
```

### Typing: `op: 5`

Sent to every member except the one typing.

```json
{ "op": 5, "data": { "user_id": "238336a2-bea1-4557-a9d1-96412cde8e19", "is_typing": true } }
```

### Error: `op: 99`

Sent only to the client whose request failed. The connection stays open.

```json
{ "op": 99, "data": { "code": 99, "reason": "Message not found" } }
```

| `reason` | Cause |
|----------|-------|
| `Message not found` | Edit/delete with an unknown `message_id`, one from another conversation, or an already-deleted message |
| `You are not the owner of this message.` | Edit/delete of someone else's message |
| `You are not a member of this conversation.` | Sending after being removed from the conversation |
| A validation string (see below) | Missing or invalid fields in `data` |

`data.code` is always `99`. Validation failures put a Python-formatted string in `reason`, not a JSON object, for example:

```
{'content': [ErrorDetail(string='This field is required.', code='required')]}
```

Show it as a generic "invalid request" in the UI rather than parsing it.

---

## 5. Constants

Copy these into the frontend. Values must match the backend exactly.

```js
// Operations (backend: apps/constants/chat.py → ChatOperations)
export const ChatOp = Object.freeze({
  // client → server
  MESSAGE_SEND: 1,
  MESSAGE_EDIT: 2,
  MESSAGE_DELETE: 3,
  MESSAGE_TYPING: 5,

  // server → client
  MESSAGE_RECEIVE: 0, // new message
  MESSAGE_EDITED: 2,  // same number as MESSAGE_EDIT
  MESSAGE_DELETED: 3, // same number as MESSAGE_DELETE
  TYPING: 5,          // same number as MESSAGE_TYPING
  ERROR: 99,
});

// Message content type (backend: apps/chat/models.py → ContentType)
export const ContentType = Object.freeze({
  TEXT: 1,
  IMAGE: 2,
  VIDEO: 3,
  AUDIO: 4,
  FILE: 5,
  URL: 6,
  OTHER: 99,
});

// WebSocket close codes (backend: apps/constants/ws_status.py → WSStatusCodes)
export const WSCloseCode = Object.freeze({
  UNAUTHORIZED: 4001,
  FORBIDDEN: 4003, // "not a member" or "Token expired"; check event.reason
});

export const MAX_MESSAGE_LENGTH = 1000;
```

### Op table

| `op` | Name | Direction | `data` |
|------|------|-----------|--------|
| `0` | MESSAGE_RECEIVE | server → client | [Message object](#message-object) |
| `1` | MESSAGE_SEND | client → server | `{content, content_type}` |
| `2` | MESSAGE_EDIT | client → server | `{message_id, content, content_type}` |
| `2` | (edited) | server → client | [Message object](#message-object) |
| `3` | MESSAGE_DELETE | client → server | `{message_id}` |
| `3` | (deleted) | server → client | `{message_id}` |
| `5` | MESSAGE_TYPING | client → server | `{is_typing}` |
| `5` | (typing) | server → client | `{user_id, is_typing}` |
| `99` | ERROR | server → client | `{code, reason}` |

### Content type

| Value | Meaning |
|-------|---------|
| `1` | Text |
| `2` | Image |
| `3` | Video |
| `4` | Audio |
| `5` | File |
| `6` | URL |
| `99` | Other |

### Defined in the backend but not used yet

Do not send or expect these; they have no effect today.

| Constant | Value | Status |
|----------|-------|--------|
| `ChatOperations.MESSAGE_MARKED_AS_READ` | `4` | No handler. Sending it breaks the connection (see [Known limitations](#7-known-limitations)). |
| `ChatOperations.MESSAGE_CREATED` / `MESSAGE_UPDATED` / `MESSAGE_DELETED` / `TYPING_UPDATE` | `10`–`13` | Never sent |
| `WSStatusCodes.CONVERSATION_NOT_FOUND` / `TOKEN_EXPIRED` | `4004` / `4005` | Never sent |

---

## 6. Frontend integration

### Flow

1. Log in → store `access` and `refresh`.
2. Join the meeting with `POST /meetings/join/`.
3. Get the meeting's `conversation_id` (see [Known limitations](#7-known-limitations)).
4. Load history with `GET /chat/messages/?conversation_id=<id>`.
5. Open the socket and apply live events on top of the history.

### Loading history

```
GET /chat/messages/?conversation_id=<conversation_id>
Authorization: Bearer <access_token>
```

Returns an array of [message objects](#message-object), oldest first, not paginated. Soft-deleted messages are included with `is_deleted: true`; filter or render them as "message deleted".

### Example client

```js
import { ChatOp, ContentType, WSCloseCode } from "./chatConstants";

export function connectChat({ baseUrl, conversationId, getAccessToken, refreshAccessToken, handlers }) {
  let ws;

  const open = () => {
    ws = new WebSocket(`${baseUrl}/ws/chat/${conversationId}/?token=${getAccessToken()}`);

    ws.onmessage = (event) => {
      const { op, data } = JSON.parse(event.data);
      switch (op) {
        case ChatOp.MESSAGE_RECEIVE: handlers.onMessage(data); break;
        case ChatOp.MESSAGE_EDITED:  handlers.onEdited(data); break;
        case ChatOp.MESSAGE_DELETED: handlers.onDeleted(data.message_id); break;
        case ChatOp.TYPING:          handlers.onTyping(data.user_id, data.is_typing); break;
        case ChatOp.ERROR:           handlers.onError(data.reason); break;
      }
    };

    ws.onclose = async (event) => {
      const tokenProblem =
        event.code === WSCloseCode.UNAUTHORIZED ||
        (event.code === WSCloseCode.FORBIDDEN && event.reason === "Token expired");

      if (tokenProblem) {
        await refreshAccessToken();
        open();
      } else if (event.code === WSCloseCode.FORBIDDEN) {
        handlers.onForbidden(); // not a member: join the meeting first
      }
    };
  };

  const send = (op, data) => ws?.readyState === WebSocket.OPEN && ws.send(JSON.stringify({ op, data }));

  open();

  return {
    sendMessage: (content) => send(ChatOp.MESSAGE_SEND, { content, content_type: ContentType.TEXT }),
    editMessage: (messageId, content) =>
      send(ChatOp.MESSAGE_EDIT, { message_id: messageId, content, content_type: ContentType.TEXT }),
    deleteMessage: (messageId) => send(ChatOp.MESSAGE_DELETE, { message_id: messageId }),
    setTyping: (isTyping) => send(ChatOp.MESSAGE_TYPING, { is_typing: isTyping }),
    close: () => ws?.close(),
  };
}
```

`baseUrl` is `ws://127.0.0.1:8000` locally, `wss://<your-domain>` in production.

### Rules for the client

- **Validate before sending**: non-empty `content`, at most 1000 characters, valid `content_type`, valid UUID for `message_id`. Invalid input produces an error frame or breaks the connection (next section).
- **Show your own messages locally** when you send them; the server does not echo them back.
- **Only send ops `1`, `2`, `3`, `5`.**
- **Only send JSON objects as text frames.**

---

## 7. Known limitations

Current server behavior the frontend has to work around. These are backend issues, not protocol rules.

| Area | Behavior | Workaround |
|------|----------|------------|
| Getting `conversation_id` | No endpoint returns it. The join response (`MeetingRoomSerializer`) has no `conversation_id` field, and `GET /chat/conversations/` fails (the view reads a `meeting_id` URL argument that does not exist). | None from the client yet; needs a backend change, for example adding `conversation_id` to the join response. |
| Sender's own new message | `op: 0` is sent with `exclude_self`, so the sender never receives the saved message or its `id`. | Render the message locally. To edit or delete it, reload history to get its `id`. |
| Invalid frames | Binary frames, invalid JSON, JSON that is not an object, and unknown `op` values (including `4`) raise an unhandled server error. The socket stops responding and may still look open. | Never send these. If the server stops responding, close and reconnect. |
| Error format | `data.code` is always `99`; validation errors arrive as a Python-formatted string in `reason`. | Show a generic message; do not parse `reason`. |
| Token expiry close code | Uses `4003`, the same as "not a member". | Check `event.reason === "Token expired"`. |
| Edited messages | `modified_at` is not updated on edit. | Use `edited_at`. |
| Deleted messages in history | `GET /chat/messages/` includes soft-deleted messages. | Filter by `is_deleted`. |
