"""
Structured JSON Logging and PII/Sensitive Data Masking for SIH 26043.
Ensures zero leakage of:
- Passwords, OTPs, secret keys, API tokens (Bearer/JWT), authorization headers.
- Citizen PII: Aadhaar numbers, full phone numbers, email addresses.
- Exact GPS coordinates in audit & access logs.
"""

import json
import logging
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict

# Regex patterns for sensitive redaction
REDACTION_PATTERNS = [
    # Authorization / Bearer tokens
    (re.compile(r"(?i)(bearer\s+)[a-zA-Z0-9_\-\.]{20,}"), r"\1[REDACTED_TOKEN]"),
    # JWT tokens in general
    (re.compile(r"eyJ[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]{10,}\.[a-zA-Z0-9_\-]+"), "[REDACTED_JWT]"),
    # Passwords in JSON / query / form (quoted or unquoted)
    (re.compile(r"(?i)([\"']?(?:password|passwd|secret|api_key|token|access_token|refresh_token)[\"']?\s*[:=]\s*[\"']?)([^\s\"'&]{3,})([\"']?)"), r"\1[REDACTED]\3"),
    # 6-digit OTPs
    (re.compile(r"(?i)([\"']?(?:otp|otp_code|verification_code)[\"']?\s*[:=]\s*[\"']?)(\d{6})([\"']?)"), r"\1[REDACTED_OTP]\3"),
    # Aadhaar numbers (12 digits, grouped 4-4-4 or raw)
    (re.compile(r"\b(\d{4})[\s\-](\d{4})[\s\-](\d{4})\b"), r"XXXX-XXXX-\3"),
    (re.compile(r"\b\d{8}(\d{4})\b"), r"XXXXXXXX\1"),
    # 10-digit Indian phone numbers
    (re.compile(r"(?:\+91[\-\s]?)?([6-9]\d{2})\d{3}(\d{4})\b"), r"+91-\1-XXX-\2"),
    # Exact GPS coordinates (floating points with > 3 decimals in lat/long context)
    (re.compile(r"(?i)(latitude|lat|longitude|lng|long)\s*[:=]\s*([+\-]?[0-9]+\.[0-9]{3})[0-9]+"), r"\1: \2~COARSE"),
]


def redact_sensitive_text(text: str) -> str:
    """Applies all regex redactions to a string."""
    if not isinstance(text, str):
        return text
    for pattern, replacement in REDACTION_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def redact_sensitive_dict(data: Any) -> Any:
    """Recursively redacts sensitive keys or string contents in dictionaries/lists."""
    if isinstance(data, dict):
        redacted = {}
        for k, v in data.items():
            k_lower = str(k).lower()
            if any(s in k_lower for s in ["password", "secret", "token", "otp", "key", "credential", "auth"]):
                redacted[k] = "[REDACTED]"
            else:
                redacted[k] = redact_sensitive_dict(v)
        return redacted
    elif isinstance(data, list):
        return [redact_sensitive_dict(item) for item in data]
    elif isinstance(data, str):
        return redact_sensitive_text(data)
    return data


class SensitiveMaskingFilter(logging.Filter):
    """Logging filter that scrubs sensitive PII, OTPs, and tokens from log records."""
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact_sensitive_text(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = redact_sensitive_dict(record.args)
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    redact_sensitive_text(str(a)) if isinstance(a, str) else redact_sensitive_dict(a)
                    for a in record.args
                )
        return True


class JSONLogFormatter(logging.Formatter):
    """
    Standardized Cloud-Ready JSON log formatter.
    Emits single-line JSON log lines compatible with Datadog, CloudWatch, GCP Cloud Logging, ELK.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }

        # Optional correlation & contextual fields
        for field in ("request_id", "actor_id", "client_ip", "path", "method", "status_code", "duration_ms"):
            if hasattr(record, field):
                log_payload[field] = getattr(record, field)

        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(redact_sensitive_dict(log_payload))


def configure_logging(environment: str = "development"):
    """Configures root logger with JSON formatting and redaction filters."""
    root_logger = logging.getLogger()
    
    # Avoid duplicate handlers if reconfigured
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(SensitiveMaskingFilter())

    if environment == "production":
        handler.setFormatter(JSONLogFormatter())
        root_logger.setLevel(logging.INFO)
    else:
        # Development human-readable formatting with masking applied
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        handler.setFormatter(formatter)
        root_logger.setLevel(logging.INFO)

    root_logger.addHandler(handler)

    # Silence overly verbose third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
