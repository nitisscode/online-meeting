# AI Service

Post-meeting intelligence pipeline (Phase 3).

## Responsibilities

- Speech-to-text (Whisper)
- Meeting summaries (LLM)
- Action item extraction
- Decision & question extraction
- Meeting title generation
- Follow-up email draft

## Communication

- Consumes jobs from Redis (published by Django/Celery)
- Writes results back to Django via REST API

## Local run (Phase 3)

```bash
cd services/ai-service
pip install -r requirements/base.txt
# uvicorn app.main:app --host 0.0.0.0 --port 8001
```

## Docker (Phase 3 profile)

```bash
docker compose --profile phase3 up ai-service
```
