# Online Meeting Platform

Production-grade AI meeting platform — Django-centric architecture with a separate AI service.

## Architecture

```
                    Client (React)
                         │
                         ▼
                API Gateway (Nginx)          ← Phase 4
                         │
                         ▼
                  Django Backend
     (REST, Auth, DB, WebSocket signaling)
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    PostgreSQL    Redis (Pub/Sub,    STUN/TURN Server
                  Cache)             (WebRTC)
                         │
                         ▼
                  Celery Workers
                         │
                         ▼
               AI Service (Python)           ← Phase 3
              Whisper · LLM · Summaries
```

## Project structure

```
online-meeting/
├── services/
│   ├── django-backend/        # REST APIs, auth, persistence, real-time signaling
│   │   ├── core/              # Main Django app (settings, URLs)
│   │   ├── apps/              # Domain apps (users, meetings, …)
│   │   ├── templates/         # Email templates
│   │   ├── manage.py
│   │   └── requirements/
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

| Phase | Scope | Command |
|-------|-------|---------|
| **1** | Django + PostgreSQL + Redis | `docker compose up` |
| **2** | Real-time signaling (WebSockets, WebRTC) inside Django | `docker compose up` |
| **3** | + AI service | `docker compose --profile phase3 up` |
| **4** | + Nginx gateway | `docker compose --profile phase4 up` |

> Start with Phase 1 only. Add features incrementally — always keep a working system.

## Local setup

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

## Docker

```bash
copy .env.example .env
docker compose up --build
```

## Development guide

Follow the step-by-step roadmap in **[docs/DEVELOPMENT_GUIDE.md](docs/DEVELOPMENT_GUIDE.md)**.

## Interview pitch

> "The core business logic runs in Django — authentication, meeting metadata, persistence, and real-time WebSocket signaling for WebRTC. AI transcription and summarization run as an independent Python service. Services communicate asynchronously through Redis and REST, containerized with Docker and deployed on AWS."
