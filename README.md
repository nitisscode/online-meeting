# Online Meeting Platform

Production-grade AI meeting platform — polyglot microservices architecture.

## Architecture

```
                    Client (React)
                         │
                         ▼
                API Gateway (Nginx)          ← Phase 4
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
   Django Backend                 Go Signaling Server
 (REST, Auth, DB)               (WebSockets, WebRTC)   ← Phase 2
         │                               │
         ▼                               ▼
   PostgreSQL                     STUN/TURN Server
         │
         ▼
   Redis (Pub/Sub, Cache)
         │
         ▼
   Celery Workers                         ← Phase 1 (Django)
         │
         ▼
   AI Service (Python)                     ← Phase 3
   Whisper · LLM · Summaries
```

## Project structure

```
online-meeting/
├── services/
│   ├── django-backend/      # Phase 1 — REST APIs, auth, persistence
│   │   ├── core/              # Main Django app (settings, URLs)
│   │   ├── apps/              # Domain apps (accounts, meetings, …)
│   │   ├── manage.py
│   │   └── requirements/
│   ├── go-signaling/          # Phase 2 — WebSocket + WebRTC signaling
│   │   ├── cmd/server/
│   │   └── internal/
│   └── ai-service/            # Phase 3 — Whisper, LLM, summaries
│       └── app/
├── docker/
│   └── nginx/                 # Phase 4 — API gateway config
├── scripts/
├── tests/
├── docs/
│   └── DEVELOPMENT_GUIDE.md
├── docker-compose.yml
└── .env.example
```

## Build phases

| Phase | Services | Command |
|-------|----------|---------|
| **1** | Django + PostgreSQL + Redis | `docker compose up` |
| **2** | + Go signaling | `docker compose --profile phase2 up` |
| **3** | + AI service | `docker compose --profile phase3 up` |
| **4** | + Nginx gateway | `docker compose --profile phase4 up` |

> Start with Phase 1 only. Add services incrementally — always keep a working system.

## Local setup (Phase 1)

```bash
cd online-meeting

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

copy .env.example .env
docker compose up -d db redis

cd services/django-backend
python manage.py migrate
python manage.py runserver
```

API: `http://localhost:8000`  
Admin: `http://localhost:8000/admin/`

## Docker (Phase 1)

```bash
copy .env.example .env
docker compose up --build
```

## Development guide

Follow the step-by-step roadmap in **[docs/DEVELOPMENT_GUIDE.md](docs/DEVELOPMENT_GUIDE.md)**.

## Interview pitch

> "The core business logic runs in Django — authentication, meeting metadata, and persistence. Real-time signaling is handled by a Go service for its concurrency model. AI transcription and summarization run as an independent Python service. Services communicate asynchronously through Redis and REST, containerized with Docker and deployed on AWS."
