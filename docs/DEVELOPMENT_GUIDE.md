# Online Meeting Platform — Development Guide

> **How to use this document:** Follow it step by step. Do not build the entire project at once. Complete one phase, review, commit, then move on. Each step ends with a suggested commit message — **wait for confirmation before proceeding**.

---

## Table of Contents

1. [Vision](#vision)
2. [System Architecture](#system-architecture)
3. [Services Overview](#services-overview)
4. [Tech Stack](#tech-stack)
5. [Project Structure](#project-structure)
6. [Inter-Service Communication](#inter-service-communication)
7. [Development Rules](#development-rules)
8. [Feature Specifications](#feature-specifications)
9. [Docker & Local Dev](#docker--local-dev)
10. [Testing](#testing)
11. [Deployment](#deployment)
12. [Documentation Deliverables](#documentation-deliverables)
13. [Development Process](#development-process)
14. [Roadmap (Step by Step)](#roadmap-step-by-step)

---

## Vision

Build a **production-grade AI meeting platform** (similar to Google Meet) using a **polyglot microservices architecture** that demonstrates system design, not just framework usage.

---

## System Architecture

```
                    Client (React)
                         │
                         ▼
                API Gateway (Nginx)              ← Phase 4
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
   Django Backend                 Go Signaling Server
 (REST, Auth, DB)               (WebSockets, WebRTC)  ← Phase 2
         │                               │
         ▼                               ▼
   PostgreSQL                     STUN/TURN Server
         │
         ▼
   Redis (Pub/Sub, Cache, Celery broker)
         │
         ├──────────────────────────────┐
         ▼                              ▼
   Celery Workers (Django)        AI Service (Python)  ← Phase 3
                                         Whisper · LLM
```

### Why microservices (and why not on day one)

| Benefit | Explanation |
|---------|-------------|
| **Right tool for the job** | Django for CRUD/auth, Go for concurrency, Python for AI |
| **Independent scaling** | Scale signaling and AI separately from REST API |
| **Interview signal** | Shows polyglot programming + distributed systems thinking |

**Caution:** Do not split everything on day one. Always keep a **working system** at each phase.

### Build progression

| Phase | What you ship | Docker command |
|-------|---------------|----------------|
| **Phase 1** | Django + PostgreSQL + Redis + Celery | `docker compose up` |
| **Phase 2** | + Go signaling service | `docker compose --profile phase2 up` |
| **Phase 3** | + AI service | `docker compose --profile phase3 up` |
| **Phase 4** | + Nginx gateway + monitoring + AWS deploy | `docker compose --profile phase4 up` |

### Interview pitch

> "The core business logic runs in Django, which manages authentication, meeting metadata, and persistence. Real-time signaling is handled by a Go service because of its concurrency model. AI transcription and summarization run as an independent Python service. The services communicate asynchronously through Redis and REST, and everything is containerized with Docker and deployed on AWS."

---

## Services Overview

### 1. Django Backend (`services/django-backend/`)

**Django excels here — keep it responsible for:**

| Domain | Examples |
|--------|----------|
| Authentication | JWT, refresh tokens, email verification, password reset |
| Meetings | Create, schedule, end, invites, waiting room |
| Participants | Roles, permissions, mute/remove |
| Chat persistence | Message history stored in PostgreSQL |
| AI results storage | Transcripts, summaries, action items (data owner) |
| REST APIs | All CRUD consumed by React frontend |
| Background jobs | Celery — email, notifications, job dispatch to AI |

**Does NOT handle:** WebSocket signaling, WebRTC media, Whisper/LLM inference.

### 2. Go Signaling Service (`services/go-signaling/`)

**Go excels here — high concurrency, low latency:**

| Responsibility | Details |
|----------------|---------|
| WebSocket connections | Thousands of simultaneous connections |
| WebRTC signaling | SDP offer/answer, ICE candidate relay |
| Room management | In-memory + Redis pub/sub for room state |
| Auth validation | Verify JWT with Django before joining room |

**Does NOT handle:** User registration, meeting CRUD, database persistence.

### 3. AI Service (`services/ai-service/`)

**Separate Python service — scale AI independently:**

| Responsibility | Details |
|----------------|---------|
| Speech-to-text | Whisper (or equivalent) |
| Summaries | LLM-generated meeting summary |
| Extraction | Action items, decisions, questions, title |
| Email draft | Follow-up email generation |

**Flow:** Django/Celery publishes job → Redis queue → AI service processes → writes results back to Django via REST API.

---

## Tech Stack

### Django Backend

| Layer | Technology |
|-------|------------|
| Language | Python 3.11+ |
| Framework | Django 5+ |
| API | Django REST Framework |
| Database | PostgreSQL |
| Cache / Queue | Redis |
| Tasks | Celery + Celery Beat |
| Auth | JWT (access + refresh) |
| Server | Gunicorn |
| Docs | drf-spectacular (OpenAPI) |

### Go Signaling Service

| Layer | Technology |
|-------|------------|
| Language | Go 1.22+ |
| WebSockets | gorilla/websocket or nhooyr/websocket |
| Config | Environment variables |

### AI Service

| Layer | Technology |
|-------|------------|
| Language | Python 3.11+ |
| Framework | FastAPI (recommended) |
| STT | Whisper |
| LLM | OpenAI / local model |
| Queue | Redis (job consumer) |

### Infrastructure

| Layer | Technology |
|-------|------------|
| Gateway | Nginx |
| Containers | Docker, Docker Compose |
| Cloud | AWS (EC2, RDS, S3, ElastiCache) |
| CI/CD | GitHub Actions |

### Frontend (later / separate)

React + Tailwind CSS

### Real-time Media

WebRTC (P2P) + STUN/TURN server

### Monitoring (Phase 4, optional)

Structured logging · Health checks · Prometheus · Grafana

---

## Project Structure

```
online-meeting/
├── services/
│   ├── django-backend/              # Phase 1 — Core backend
│   │   ├── core/                    # Main Django app (settings, URLs)
│   │   │   ├── settings.py
│   │   │   ├── urls.py
│   │   │   ├── wsgi.py
│   │   │   └── apps.py
│   │   ├── apps/                    # Domain apps
│   │   │   ├── common/
│   │   │   ├── accounts/
│   │   │   ├── meetings/
│   │   │   ├── participants/
│   │   │   ├── chat/
│   │   │   ├── notifications/
│   │   │   ├── transcriptions/
│   │   │   ├── ai/                  # AI *results* models (not inference)
│   │   │   ├── recordings/
│   │   │   └── ...
│   │   ├── manage.py
│   │   ├── requirements/
│   │   └── Dockerfile
│   │
│   ├── go-signaling/                # Phase 2 — Real-time
│   │   ├── cmd/server/              # Entry point
│   │   ├── internal/
│   │   │   ├── websocket/           # WS handlers
│   │   │   ├── signaling/           # WebRTC SDP/ICE logic
│   │   │   ├── room/                # Room state management
│   │   │   └── auth/                # JWT validation via Django
│   │   ├── go.mod
│   │   └── Dockerfile
│   │
│   └── ai-service/                  # Phase 3 — AI pipeline
│       ├── app/
│       │   ├── main.py              # FastAPI entry
│       │   ├── workers/             # Redis job consumers
│       │   ├── transcription/       # Whisper
│       │   └── summarization/       # LLM
│       ├── requirements/
│       └── Dockerfile
│
├── docker/
│   └── nginx/                       # Phase 4 — API gateway
├── scripts/                         # Utility & deploy scripts
├── tests/                           # Cross-service integration tests
├── docs/
│   ├── DEVELOPMENT_GUIDE.md         # This file
│   └── architecture/                # Diagrams, ERD, sequences
│
├── docker-compose.yml
├── .env.example
└── README.md
```

### Django app internal structure

Each app under `services/django-backend/apps/`:

```
apps/meetings/
├── models/
├── services/          # Business logic
├── selectors/         # Read queries
├── api/               # DRF views, serializers, urls
├── tasks.py           # Celery tasks
├── migrations/
└── tests/
```

### Go service internal structure

```
internal/
├── websocket/         # Connection upgrade, message routing
├── signaling/         # offer, answer, ice-candidate handlers
├── room/              # Room registry, participant tracking
└── auth/              # Token validation (calls Django)
```

---

## Inter-Service Communication

| From → To | Protocol | Purpose |
|-----------|----------|---------|
| React → Nginx → Django | HTTP/REST | CRUD, auth |
| React → Nginx → Go | WebSocket | Signaling, live events |
| Go → Django | HTTP/REST | Validate JWT, fetch meeting metadata |
| Django → AI Service | Redis pub/sub | Dispatch transcription/summary jobs |
| AI Service → Django | HTTP/REST | Persist transcript & AI output |
| Go ↔ Go (multi-instance) | Redis pub/sub | Broadcast across signaling nodes |

### Redis database allocation

| DB | Consumer |
|----|----------|
| `0` | Django cache + Celery broker |
| `1` | Go signaling pub/sub |
| `2` | AI service job queue |

---

## Development Rules

### Django (always)

- [ ] Class-based DRF views where appropriate
- [ ] Business logic in **services**, not views
- [ ] Read queries in **selectors**
- [ ] UUID primary keys, timezone-aware timestamps
- [ ] Soft delete where appropriate
- [ ] Database indexes on queried fields
- [ ] `select_related()` / `prefetch_related()` — no N+1
- [ ] `transaction.atomic()` for multi-write operations
- [ ] Type hints on services and selectors
- [ ] PEP 8, small functions, meaningful commits

### Go (always)

- [ ] Keep handlers thin — logic in `internal/` packages
- [ ] Context propagation for cancellation/timeouts
- [ ] Graceful shutdown
- [ ] Structured logging
- [ ] Health check endpoint (`/health`)

### AI Service (always)

- [ ] Stateless workers — state lives in Django/PostgreSQL
- [ ] Idempotent job processing
- [ ] Retry with backoff on transient failures
- [ ] Never store secrets in code

### Per-PR checklist

- [ ] No business logic in views/handlers
- [ ] Tests added or updated
- [ ] `.env.example` updated for new env vars
- [ ] No secrets committed

---

## Feature Specifications

### Service ownership matrix

| Feature | Django | Go | AI Service |
|---------|--------|-----|------------|
| JWT auth | ✅ | validates | — |
| Meeting CRUD | ✅ | — | — |
| Participants | ✅ | live state | — |
| Chat history | ✅ persist | ✅ relay | — |
| WebRTC signaling | — | ✅ | — |
| Transcription | dispatches | — | ✅ Whisper |
| Summaries | stores | — | ✅ LLM |
| Recordings metadata | ✅ | — | processes |
| Notifications | ✅ Celery | — | — |

### Authentication (Django — `apps/accounts/`)

JWT access + refresh · Email verification · Password reset · Social login (optional)

### Meetings (Django — `apps/meetings/`)

Create · Join · Leave · End · Schedule · Invites · Waiting room · Host permissions · Password · Public/private

### Chat

- **Go:** Real-time delivery, typing indicators, read receipts (ephemeral)
- **Django:** Message persistence, history API, file metadata

### Video (Go + WebRTC)

Audio · Video · Screen share · Camera/mic toggle · Participant grid (frontend) · Active speaker (frontend)

Signaling via **Go WebSockets**. Media is **P2P WebRTC** with STUN/TURN.

### AI (AI Service + Django storage)

After meeting ends: audio → text → summary → action items → title → follow-up email → stored in PostgreSQL via Django REST.

---

## Docker & Local Dev

### Phase 1 (default)

```bash
copy .env.example .env
docker compose up --build
# Django: http://localhost:8000
```

### Phase 2

```bash
docker compose --profile phase2 up --build
# Go signaling: ws://localhost:8080
```

### Phase 3

```bash
docker compose --profile phase3 up --build
# AI service: http://localhost:8001
```

### Phase 4

```bash
docker compose --profile phase2 --profile phase3 --profile phase4 up --build
# Nginx gateway: http://localhost
```

### Local Django (without Docker)

```bash
.venv\Scripts\activate
pip install -r services/django-backend/requirements/development.txt
docker compose up -d db redis
cd services/django-backend
python manage.py migrate
python manage.py runserver
```

---

## Testing

| Type | Location |
|------|----------|
| Django unit/API tests | `services/django-backend/apps/<app>/tests/` |
| Go unit tests | `services/go-signaling/internal/**/**_test.go` |
| AI service tests | `services/ai-service/tests/` |
| Cross-service integration | `tests/` |

**Target:** ≥ 80% coverage on Django; Go and AI services tested per package.

---

## Deployment

### AWS (Phase 4)

```
Internet → Nginx (EC2)
              ├── Django (Gunicorn) → RDS PostgreSQL
              ├── Go Signaling       → ElastiCache Redis
              └── AI Service         → S3 (recordings)
```

| Component | AWS Service |
|-----------|-------------|
| All services | EC2 or ECS |
| Database | RDS PostgreSQL |
| Cache / queues | ElastiCache Redis |
| Files | S3 |
| Secrets | Env vars / Secrets Manager |
| CI/CD | GitHub Actions |

---

## Documentation Deliverables

| Document | Location |
|----------|----------|
| README | `/README.md` |
| Development guide | `/docs/DEVELOPMENT_GUIDE.md` |
| Architecture diagrams | `/docs/architecture/` |
| Sequence diagrams | `/docs/architecture/sequences/` |
| Database ERD | `/docs/architecture/database.md` |
| Deployment guide | `/docs/DEPLOYMENT.md` |
| API docs | Swagger at `/api/docs/` |

---

## Development Process

```
1. Explain WHY
2. Show folder structure
3. Generate production-quality code
4. Explain the code
5. Suggest a Git commit message
6. WAIT for confirmation
```

### Commit format

```
<type>(<scope>): <summary>

[optional body]
```

**Scopes:** `django`, `go-signaling`, `ai-service`, `docker`, `docs`, `ci`

---

## Roadmap (Step by Step)

### Phase 0 — Monorepo Foundation ✅ (Done)

- [x] Multi-service folder structure (`services/django-backend`, `go-signaling`, `ai-service`)
- [x] Django scaffold with `core/` + `apps/`
- [x] Docker Compose with phased profiles
- [x] Development guide

---

### Phase 1 — Django Core Backend

> **Goal:** Working REST API with auth, meetings, and Celery. No Go or AI yet.

#### Step 1.1 — `apps/common/`

Shared base models (UUID, timestamps, soft delete), exceptions, pagination.

**Commit:** `feat(django): add common base models and shared utilities`

#### Step 1.2 — `apps/accounts/` (User model)

Custom User (email login) — must exist before first migration.

**Commit:** `feat(django): add custom User model with email authentication`

#### Step 1.3 — JWT Authentication

`djangorestframework-simplejwt` — login, refresh, logout.

**Commit:** `feat(django): implement JWT auth with refresh token rotation`

#### Step 1.4 — Email verification & password reset

Async email via Celery.

**Commit:** `feat(django): add email verification and password reset`

#### Step 1.5 — `apps/meetings/` + `apps/participants/`

Meeting CRUD, join/leave, waiting room, host permissions.

**Commit:** `feat(django): add meetings and participant management APIs`

#### Step 1.6 — `apps/chat/` (persistence only)

Message model + history REST API. Real-time delivery comes in Phase 2.

**Commit:** `feat(django): add chat message persistence and history API`

#### Step 1.7 — Celery setup

Worker + Beat in Docker Compose. Email and reminder tasks.

**Commit:** `chore(django): configure Celery worker and beat services`

---

### Phase 2 — Go Signaling Service

> **Goal:** WebSocket signaling for WebRTC. Django still owns all data.

#### Step 2.1 — Go project structure

`internal/websocket`, `internal/signaling`, `internal/room`, `internal/auth`.

**Commit:** `feat(go-signaling): scaffold Go signaling service structure`

#### Step 2.2 — JWT validation via Django

Go validates tokens by calling Django REST endpoint.

**Commit:** `feat(go-signaling): add JWT validation against Django API`

#### Step 2.3 — WebSocket room management

Connect, disconnect, room join/leave, Redis pub/sub for multi-node.

**Commit:** `feat(go-signaling): add WebSocket room management with Redis`

#### Step 2.4 — WebRTC signaling

SDP offer/answer and ICE candidate relay.

**Commit:** `feat(go-signaling): implement WebRTC signaling handlers`

#### Step 2.5 — Real-time chat relay

Go relays chat events; Django persists via REST callback.

**Commit:** `feat(go-signaling): add real-time chat message relay`

#### Step 2.6 — STUN/TURN configuration

Env-driven STUN/TURN server config exposed to clients.

**Commit:** `feat(go-signaling): add STUN/TURN server configuration`

---

### Phase 3 — AI Service

> **Goal:** Post-meeting intelligence pipeline, independent of Django runtime.

#### Step 3.1 — AI service scaffold

FastAPI app, Redis job consumer, health check.

**Commit:** `feat(ai-service): scaffold FastAPI service with Redis consumer`

#### Step 3.2 — Whisper transcription

Audio → text, POST result to Django.

**Commit:** `feat(ai-service): add Whisper speech-to-text pipeline`

#### Step 3.3 — LLM summarization

Summary, decisions, action items, questions, title, follow-up email.

**Commit:** `feat(ai-service): add LLM meeting summary and extraction`

#### Step 3.4 — Django integration

`apps/transcriptions/` + `apps/ai/` models, Celery dispatch, REST retrieval APIs.

**Commit:** `feat(django): integrate AI service results storage and APIs`

---

### Phase 4 — Production Hardening & Deployment

#### Step 4.1 — Nginx API gateway

Route `/api/` → Django, `/ws/` → Go.

**Commit:** `chore(docker): add Nginx API gateway routing`

#### Step 4.2 — OpenAPI docs + test coverage

drf-spectacular, 80% coverage target.

**Commit:** `docs(django): add OpenAPI documentation and expand test suite`

#### Step 4.3 — GitHub Actions CI/CD

Test all services, build images, deploy to AWS.

**Commit:** `ci: add GitHub Actions pipeline for multi-service deploy`

#### Step 4.4 — AWS deployment

EC2, RDS, S3, ElastiCache. Deployment guide.

**Commit:** `docs: add AWS deployment guide`

#### Step 4.5 — Monitoring (optional)

Structured logging, health checks, Prometheus/Grafana.

**Commit:** `chore: add monitoring and health check endpoints`

---

## Quick Reference

| Question | Answer |
|----------|--------|
| Where is Django? | `services/django-backend/` |
| Where are Django apps? | `services/django-backend/apps/<name>/` |
| Where is Go signaling? | `services/go-signaling/` |
| Where is AI? | `services/ai-service/` |
| Django settings? | `services/django-backend/core/settings.py` |
| Business logic? | `apps/<name>/services/` |
| Real-time signaling? | Go service (not Django) |
| AI inference? | AI service (not Django) |
| AI data storage? | Django PostgreSQL |
| Inter-service comms? | REST + Redis pub/sub |
| Phase 1 docker? | `docker compose up` |
| Add Go? | `docker compose --profile phase2 up` |
| Add AI? | `docker compose --profile phase3 up` |

---

*Last updated: multi-service architecture restructure.*
