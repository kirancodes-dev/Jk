# Production Dockerfile for SIH 2026 Portal
# Government of Jharkhand — Department of Higher & Technical Education

# ---- Stage 1: Flutter web app ------------------------------------------------
# Pinned to the Flutter release the app is developed and tested with (Dart 3.11.5).
FROM ghcr.io/cirruslabs/flutter:3.41.9 AS web

# EVALUATOR_MODE=true adds the one-tap demo persona picker to the login screen;
# only the demo deployment sets it. Render passes service env vars as build args.
ARG EVALUATOR_MODE=false

WORKDIR /src/frontend
COPY frontend/pubspec.yaml frontend/pubspec.lock ./
RUN flutter pub get
COPY frontend/ ./
RUN flutter build web --release --dart-define=EVALUATOR_MODE=${EVALUATOR_MODE}

# ---- Stage 2: API runtime (serves the web app too) ---------------------------
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
COPY docker-entrypoint.sh /app/docker-entrypoint.sh

# Flutter web bundle from stage 1, served by FastAPI at /
COPY --from=web /src/frontend/build/web /app/frontend/build/web

# Create storage upload directories with non-root ownership
RUN mkdir -p /app/uploads/demo /app/uploads/challenges && \
    chmod +x /app/docker-entrypoint.sh && \
    chown -R appuser:appgroup /app

# Run as non-root user
USER appuser

EXPOSE 8008

# Healthcheck contract using /live probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8008}/live || exit 1

# Optional migrations and demo seeding, then Uvicorn (WEB_CONCURRENCY workers, default 4)
CMD ["/app/docker-entrypoint.sh"]
