FROM python:3.10-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PORT 7860

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from backend and install
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Create data directory
RUN mkdir -p /app/data

# Final working directory for the app
WORKDIR /app/backend

# Expose port
EXPOSE 7860

# Run the backend app
CMD ["gunicorn", "--bind", "0.0.0.0:7860", "--timeout", "120", "--workers", "1", "app:app"]
