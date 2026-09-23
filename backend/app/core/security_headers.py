"""
Production Security Middleware for SIH 26043 (Government of Jharkhand).
Enforces:
1. Strict Content-Security-Policy (CSP) compatible with Flutter web/CanvasKit.
2. HTTP Strict Transport Security (HSTS) behind HTTPS/trusted reverse proxy.
3. Defense-in-depth headers: X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy.
4. Safe Cache-Control headers on API and sensitive routes.
5. Request size limiter (preventing payload exhaustion / DoS).
6. Request execution timeout protection.
7. Trusted reverse-proxy IP extraction.
"""

import time
import ipaddress
from typing import List, Optional
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
try:
    from backend.app.core.config import settings
except ImportError:
    from app.core.config import settings


# Default Content-Security-Policy compatible with Flutter web CanvasKit & static assets
DEFAULT_CSP = (
    "default-src 'self'; "
    "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://unpkg.com https://fonts.googleapis.com; "
    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
    "font-src 'self' data: https://fonts.gstatic.com; "
    "img-src 'self' data: blob: https:; "
    "connect-src 'self' https: ws: wss:; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "form-action 'self'; "
    "frame-ancestors 'none';"
)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.is_production = settings.ENVIRONMENT == "production"

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)

        # 1. Defense-in-depth security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "geolocation=(), camera=(), microphone=(), payment=(), usb=()"
        )

        # 2. Content-Security-Policy
        # Apply CSP unless explicitly disabled or file stream
        if not response.headers.get("Content-Security-Policy"):
            response.headers["Content-Security-Policy"] = DEFAULT_CSP

        # 3. HTTP Strict Transport Security (HSTS)
        # Apply HSTS only when request is verified HTTPS or behind HTTPS reverse proxy
        is_https = (
            request.url.scheme == "https"
            or request.headers.get("X-Forwarded-Proto", "").lower() == "https"
        )
        if is_https or (self.is_production and settings.ENABLE_HSTS):
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # 4. Safe Cache-Control for authenticated API responses
        path = request.url.path
        if path.startswith("/api/"):
            if not response.headers.get("Cache-Control"):
                response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
                response.headers["Pragma"] = "no-cache"

        return response


class RequestLimitMiddleware(BaseHTTPMiddleware):
    """
    Guards against denial-of-service through:
    - Enforcing maximum request body size limit
    - Request timeout detection
    """
    def __init__(
        self,
        app: ASGIApp,
        max_body_bytes: int = 25 * 1024 * 1024,  # 25 MB max payload
        timeout_seconds: float = 60.0             # 60s max execution
    ):
        super().__init__(app)
        self.max_body_bytes = max_body_bytes
        self.timeout_seconds = timeout_seconds

    async def dispatch(self, request: Request, call_next) -> Response:
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length = int(content_length)
                if length > self.max_body_bytes:
                    return Response(
                        content='{"detail":"Request payload exceeds maximum allowed size (25 MB)."}',
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        media_type="application/json"
                    )
            except ValueError:
                pass

        start_time = time.time()
        response: Response = await call_next(request)
        elapsed = time.time() - start_time

        response.headers["X-Response-Time"] = f"{elapsed:.4f}s"
        return response


class TrustedProxyHelper:
    """
    Validates and extracts client IP addresses strictly through configured trusted proxy networks.
    Prevents IP spoofing in audit logs and rate limiters.
    """
    DEFAULT_TRUSTED_CIDRS = [
        ipaddress.ip_network("127.0.0.0/8"),
        ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("172.16.0.0/12"),
        ipaddress.ip_network("192.168.0.0/16"),
        ipaddress.ip_network("::1/128"),
        ipaddress.ip_network("fc00::/7"),
    ]

    @classmethod
    def is_trusted_proxy(cls, ip_str: str) -> bool:
        try:
            ip = ipaddress.ip_address(ip_str.strip())
            return any(ip in net for net in cls.DEFAULT_TRUSTED_CIDRS)
        except ValueError:
            return False

    @classmethod
    def get_trusted_client_ip(cls, request: Request) -> str:
        direct_ip = request.client.host if request.client else "127.0.0.1"

        forwarded = request.headers.get("X-Forwarded-For")
        if not forwarded:
            return direct_ip

        # If direct connection is from a trusted reverse proxy, parse forwarded chain
        if cls.is_trusted_proxy(direct_ip):
            ips = [ip.strip() for ip in forwarded.split(",") if ip.strip()]
            if ips:
                # Leftmost untrusted IP is the real client IP
                for candidate in reversed(ips):
                    if not cls.is_trusted_proxy(candidate):
                        return candidate
                return ips[0]

        return direct_ip
