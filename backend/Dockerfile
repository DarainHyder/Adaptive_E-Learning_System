# Standalone backend image (build context: backend/). The repo-root Dockerfile is the one HF Spaces uses.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=7860 \
    DATA_DIR=/app/data

RUN useradd -m -u 1000 user
WORKDIR /app/backend

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY --chown=user . .
RUN mkdir -p /app/data && chown -R user /app/data

USER user
EXPOSE 7860
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "1", "--threads", "8", "--worker-class", "gthread", "--timeout", "180", "app:app"]
