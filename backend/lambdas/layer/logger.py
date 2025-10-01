"""
Sake Sensei - Lambda Logger

Structured logging for Lambda functions.
"""

import json
import logging
import os
from typing import Any


class StructuredLogger:
    """Structured logger for Lambda functions with JSON output."""

    def __init__(self, name: str, level: str | None = None) -> None:
        """Initialize structured logger.

        Args:
            name: Logger name (usually __name__)
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logger = logging.getLogger(name)
        log_level = level or os.getenv("LOG_LEVEL", "INFO")
        self.logger.setLevel(getattr(logging, log_level.upper()))

        # Remove existing handlers
        self.logger.handlers.clear()

        # Add structured JSON handler
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)

    def _log(self, level: str, message: str, extra: dict[str, Any] | None = None) -> None:
        """Log message with extra context.

        Args:
            level: Log level
            message: Log message
            extra: Additional context to include
        """
        log_data = {"message": message}
        if extra:
            log_data.update(extra)

        getattr(self.logger, level)(json.dumps(log_data))

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        self._log("debug", message, kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        self._log("info", message, kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        self._log("warning", message, kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        self._log("error", message, kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message."""
        self._log("critical", message, kwargs)


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: Log record

        Returns:
            JSON formatted log string
        """
        log_data = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra"):
            log_data.update(record.extra)

        return json.dumps(log_data)


def get_logger(name: str, level: str | None = None) -> StructuredLogger:
    """Get or create a structured logger.

    Args:
        name: Logger name (usually __name__)
        level: Log level (optional)

    Returns:
        StructuredLogger instance

    Example:
        logger = get_logger(__name__)
        logger.info("Processing request", user_id="user_123", action="get_sake")
    """
    return StructuredLogger(name, level)
