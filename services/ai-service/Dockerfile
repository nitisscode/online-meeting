FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements/base.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt || true

COPY . .

EXPOSE 8001

# Replace with: CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
CMD ["python", "-c", "print('AI service scaffold — implement in Phase 3')"]
