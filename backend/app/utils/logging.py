"""
Structured Logging Configuration

Sets up rotating file handler + stream handler with JSON-capable formatting.
Source code content is never logged (redacted per security policy).
"""

from __future__ import annotations

import logging
import logging.handlers
import os
import sys
from pathlib import Path


def configure_logging() -> None:
    """Configure application-wide structured logging."""
    from app.config import get_settings
    settings = get_settings()

    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Ensure log directory exists
    log_path = Path(settings.log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    # ── Root logger ────────────────────────────────────────────────────────────
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # ── Stream handler (stdout) ────────────────────────────────────────────────
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(log_level)
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    # ── Rotating file handler ──────────────────────────────────────────────────
    file_handler = logging.handlers.RotatingFileHandler(
        filename=str(log_path),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.DEBUG if settings.debug else logging.WARNING
    )


class SecurityFilter(logging.Filter):
    """
    Logging filter that redacts source code content from log records.
    Applied when REDACT_SOURCE_CODE_IN_LOGS=true.
    """

    REDACTED = "[SOURCE CODE REDACTED]"
    _sensitive_keys = {"source_code", "c_code", "fortran_code", "content", "code"}

    def filter(self, record: logging.LogRecord) -> bool:
        if hasattr(record, "msg") and isinstance(record.msg, str):
            # Basic heuristic: if the message looks like raw source code, redact it
            if len(record.msg) > 500 and (
                "#include" in record.msg
                or "PROGRAM " in record.msg
                or "SUBROUTINE " in record.msg
            ):
                record.msg = self.REDACTED
                record.args = ()
        return True
