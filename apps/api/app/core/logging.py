"""Structured JSON logging with correlation ID injection across service boundaries."""

import json
import logging
import sys
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Dict, Optional
import uuid

# Context variable for request correlation ID
correlation_id_ctx: ContextVar[Optional[str]] = ContextVar("correlation_id", default=None)


def get_correlation_id() -> str:
    cid = correlation_id_ctx.get()
    if not cid:
        cid = str(uuid.uuid4())
        correlation_id_ctx.set(cid)
    return cid


def set_correlation_id(cid: str) -> None:
    correlation_id_ctx.set(cid)


class JSONFormatter(logging.Formatter):
    """Custom formatter that emits structured JSON records."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": correlation_id_ctx.get() or "system",
        }

        # Include exception details if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Include extra fields passed to logger
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log_data.update(record.extra_data)

        # Filter out sensitive fields
        sanitized = self._sanitize(log_data)
        return json.dumps(sanitized)

    def _sanitize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        sensitive_keys = {"password", "secret", "token", "jwt", "api_key", "authorization"}
        cleaned = {}
        for k, v in data.items():
            if any(s in k.lower() for s in sensitive_keys):
                cleaned[k] = "[REDACTED]"
            elif isinstance(v, dict):
                cleaned[k] = self._sanitize(v)
            else:
                cleaned[k] = v
        return cleaned


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger("tradly")
    logger.setLevel(level)
    logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    logger.propagate = False
    return logger


logger = setup_logging()
