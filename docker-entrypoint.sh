#!/bin/sh
# Container entrypoint: one-shot startup tasks, then the API server.
# RUN_MIGRATIONS_ON_START=true applies Alembic migrations first (on for the
# single-instance demo; leave off where several replicas start together and
# run migrations as a separate release step instead). With DEMO_MODE=true the
# demo data is seeded here, before the workers start.
set -e

python -m backend.app.services.demo_bootstrap

exec python -m uvicorn backend.app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8008}" \
  --workers "${WEB_CONCURRENCY:-4}"
