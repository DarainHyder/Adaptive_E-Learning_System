# Hugging Face Space image (sdk: docker, app_port: 7860). Serves the Flask API in backend/.
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=7860

# HF Spaces run containers as uid 1000
RUN useradd -m -u 1000 user
WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install -r /app/backend/requirements.txt

COPY --chown=user backend /app/backend
RUN mkdir -p /app/data && chown -R user /app/data

USER user
WORKDIR /app/backend
EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7860/api/health')"

# One process (the DB seeding and the in-process metrics assume it); threads for concurrency.
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--workers", "1", "--threads", "8", "--worker-class", "gthread", "--timeout", "180", "app:app"]
