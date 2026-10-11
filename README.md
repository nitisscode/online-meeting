# Online Meeting Platform

Production-grade AI meeting platform — a single Django project handling REST, real-time signaling, and AI.

## Architecture

```
                    Client (React)
                         │
                         ▼
                API Gateway (Nginx)          ← Phase 4
                         │
                         ▼
                  Django Backend
   (REST, Auth, DB, WebSocket signaling, AI)
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
    PostgreSQL    Redis (Pub/Sub,    STUN/TURN Server
                  Cache, Broker)     (WebRTC)
                         │
                         ▼
                  Celery Workers
           (Whisper · LLM · Summaries)
```

## Project structure

```
online-meeting/
├── apps/                  # Domain apps
│   ├── users/             # Custom user model, JWT auth
│   ├── meetings/          # Meetings, participants, settings
│   └── ai/                # Transcription, summaries (Phase 3)
├── core/                  # Project config (settings, URLs, WSGI/ASGI)
├── templates/             # Email templates
├── docker/
│   └── nginx/             # Phase 4 — API gateway config
├── docs/
│   └── DEVELOPMENT_GUIDE.md
├── manage.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## Build phases

| Phase | Scope | Command |
|-------|-------|---------|
| **1** | Django + PostgreSQL + Redis | `docker compose up` |
| **2** | Real-time signaling (WebSockets, WebRTC) | `docker compose up` |
| **3** | AI transcription and summaries (`apps/ai`) | `docker compose up` |
| **4** | + Nginx gateway | `docker compose --profile phase4 up` |

> Add features incrementally — always keep a working system.

## Local setup

```bash
cd online-meeting

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

copy .env.example .env
docker compose up -d db redis

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

> "The platform runs as a single Django project — authentication, meeting metadata, persistence, real-time WebSocket signaling for WebRTC, and AI transcription and summarization. Long-running AI work runs in Celery workers over Redis. Everything is containerized with Docker and deployed on AWS."
