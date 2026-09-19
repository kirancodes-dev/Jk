# Multi-stage production Dockerfile for SIH26043
# Department of Higher & Technical Education, Government of Jharkhand

FROM python:3.12-slim AS runtime

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8008 \
    DEMO_MODE=false

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy application source code
COPY backend /app/backend
COPY frontend/build/web /app/frontend/build/web
COPY database /app/database
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini
COPY .env.example /app/.env

# Create media uploads directories
RUN mkdir -p /app/uploads/demo /app/uploads/challenges

# Expose port
EXPOSE 8008

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8008/health || exit 1

# Start production server with Uvicorn
CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8008", "--workers", "4"]
