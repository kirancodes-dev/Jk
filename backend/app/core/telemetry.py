"""
Prometheus Metrics, Health Probes, and Application Telemetry for SIH 26043.
Provides:
- Standard /metrics endpoint in Prometheus exposition format.
- Request rate, latency histogram, and status code distribution.
- Background worker queue depths and database connection telemetry.
- Security event tracking (rate limits, auth failures, quarantine detections).
"""

import time
from typing import Dict, Any, Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

try:
    from prometheus_client import (
        Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST,
        CollectorRegistry, REGISTRY
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


if PROMETHEUS_AVAILABLE:
    # HTTP Metrics
    HTTP_REQUESTS_TOTAL = Counter(
        "http_requests_total",
        "Total count of HTTP requests processed",
        ["method", "endpoint", "status_code"]
    )
    HTTP_REQUEST_DURATION_SECONDS = Histogram(
        "http_request_duration_seconds",
        "Histogram of HTTP request processing latency in seconds",
        ["method", "endpoint"],
        buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
    )

    # Queue & Worker Metrics
    QUEUE_DEPTH_GAUGE = Gauge(
        "backend_queue_depth",
        "Number of pending items in background queues",
        ["queue_name"]
    )

    # Security Metrics
    SECURITY_EVENTS_TOTAL = Counter(
        "security_events_total",
        "Count of security anomalies, auth violations, and quarantine triggers",
        ["event_type"]
    )

    # Database Pool Status
    DB_POOL_ACTIVE_GAUGE = Gauge(
        "database_pool_active_connections",
        "Number of currently active/checked out database connections"
    )
else:
    # Minimal fallback in-memory registry if prometheus_client is not installed
    class _MockMetric:
        def __init__(self, *args, **kwargs):
            self.value = 0
            self.records = {}
        def labels(self, *args, **kwargs):
            return self
        def inc(self, amount=1):
            self.value += amount
        def observe(self, amount):
            self.value = amount
        def set(self, val):
            self.value = val

    HTTP_REQUESTS_TOTAL = _MockMetric()
    HTTP_REQUEST_DURATION_SECONDS = _MockMetric()
    QUEUE_DEPTH_GAUGE = _MockMetric()
    SECURITY_EVENTS_TOTAL = _MockMetric()
    DB_POOL_ACTIVE_GAUGE = _MockMetric()
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"

    def generate_latest():
        return b"# Telemetry metrics fallback\nbackend_status_up 1\n"


class PrometheusMetricsMiddleware(BaseHTTPMiddleware):
    """Measures latency and request counts across all endpoints."""
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next) -> Response:
        # Avoid tracking metrics endpoint itself to prevent loop inflation
        path = request.url.path
        if path in ("/metrics", "/live", "/ready"):
            return await call_next(request)

        method = request.method
        start_time = time.time()

        status_code = 500
        try:
            response: Response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            elapsed = time.time() - start_time
            # Normalize high-cardinality endpoint paths (e.g. replace IDs with {id})
            endpoint = self._normalize_endpoint(path)

            if PROMETHEUS_AVAILABLE:
                HTTP_REQUESTS_TOTAL.labels(
                    method=method,
                    endpoint=endpoint,
                    status_code=str(status_code)
                ).inc()
                HTTP_REQUEST_DURATION_SECONDS.labels(
                    method=method,
                    endpoint=endpoint
                ).observe(elapsed)

    @staticmethod
    def _normalize_endpoint(path: str) -> str:
        # Standardize numeric IDs and UUIDs to avoid cardinality explosion in Prometheus
        parts = path.strip("/").split("/")
        normalized = []
        for p in parts:
            if p.isdigit():
                normalized.append("{id}")
            elif len(p) in (32, 36) and all(c in "0123456789abcdefABCDEF-" for c in p):
                normalized.append("{uuid}")
            else:
                normalized.append(p)
        return "/" + "/".join(normalized)


def track_security_event(event_type: str):
    """Tracks security events such as brute_force_attempt, invalid_token, eicar_malware_detected."""
    if PROMETHEUS_AVAILABLE:
        SECURITY_EVENTS_TOTAL.labels(event_type=event_type).inc()


def update_queue_depth(queue_name: str, count: int):
    """Updates background worker queue gauge."""
    if PROMETHEUS_AVAILABLE:
        QUEUE_DEPTH_GAUGE.labels(queue_name=queue_name).set(count)


def get_metrics_response() -> Response:
    """Returns the Prometheus-formatted metrics payload."""
    if PROMETHEUS_AVAILABLE:
        data = generate_latest(REGISTRY)
        return Response(content=data, media_type=CONTENT_TYPE_LATEST)
    return Response(content=b"# Prometheus metrics unavailable\n", media_type="text/plain")
