# Production Dockerfile for SIH 2026 Portal
# Government of Jharkhand — Department of Higher & Technical Education
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8008

WORKDIR /app

# Install runtime system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Install build dependencies, install requirements, then remove build tools
COPY backend/requirements.txt /app/backend/requirements.txt
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && pip install --no-cache-dir -r /app/backend/requirements.txt \
    && apt-get purge -y build-essential libpq-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# Create non-root system user and group (UID/GID 10001)
RUN groupadd -r -g 10001 appgroup && \
    useradd -r -u 10001 -g appgroup -s /sbin/nologin -d /app appuser

# Copy application source code (secrets must be provided via environment, not baked in)
COPY backend /app/backend
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini
COPY database /app/database

# Handle frontend assets: copy if prebuilt artifacts exist; otherwise initialize web dir
COPY frontend /tmp/frontend_src
RUN mkdir -p /app/frontend/build/web && \
    if [ -d /tmp/frontend_src/build/web ] && [ -f /tmp/frontend_src/build/web/index.html ]; then \
        cp -r /tmp/frontend_src/build/web/* /app/frontend/build/web/; \
    fi && \
    rm -rf /tmp/frontend_src

# Create storage upload directories with non-root ownership
RUN mkdir -p /app/uploads/demo /app/uploads/challenges && \
    chown -R appuser:appgroup /app

# Run as non-root user
USER appuser

EXPOSE 8008

# Healthcheck contract using /live probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8008/live || exit 1

# Start production server with Uvicorn
CMD ["python", "-m", "uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8008", "--workers", "4"]

