# Go Signaling Service

Real-time WebSocket signaling for WebRTC (Phase 2).

## Responsibilities

- WebSocket connections for meeting rooms
- WebRTC SDP offer/answer exchange
- ICE candidate relay
- High-concurrency connection management

## Does NOT handle

- User authentication (validated via Django REST API)
- Meeting metadata persistence (Django)
- Chat message storage (Django)

## Local run (Phase 2)

```bash
cd services/go-signaling
go run ./cmd/server
```

## Docker (Phase 2 profile)

```bash
docker compose --profile phase2 up go-signaling
```
