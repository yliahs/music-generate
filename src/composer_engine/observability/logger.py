"""Structured logging for Composer Engine.

Outputs to stderr (not stdout) to avoid interfering with MCP communication.
Log level controlled via COMPOSER_LOG_LEVEL env var (default: INFO).
Optional file output via COMPOSER_LOG_FILE env var.
"""

import logging
import os
import sys

LOG_FORMAT = "[%(asctime)s] [%(levelname)-5s] [%(tag)-6s] %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_logger: logging.Logger | None = None


class _TagFilter(logging.Filter):
    """Injects a default 'tag' field into log records."""

    def __init__(self, default_tag: str = "SYSTEM"):
        super().__init__()
        self.default_tag = default_tag

    def filter(self, record):
        if not hasattr(record, "tag"):
            record.tag = self.default_tag
        return True


def setup_logger() -> logging.Logger:
    """Initialize the global composer_engine logger."""
    global _logger
    if _logger is not None:
        return _logger

    logger = logging.getLogger("composer_engine")
    logger.handlers.clear()

    level_name = os.environ.get("COMPOSER_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    logger.setLevel(level)

    tag_filter = _TagFilter()

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
    stderr_handler.addFilter(tag_filter)
    logger.addHandler(stderr_handler)

    log_file = os.environ.get("COMPOSER_LOG_FILE", "")
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT, DATE_FORMAT))
        file_handler.addFilter(tag_filter)
        logger.addHandler(file_handler)

    _logger = logger
    return logger


def get_logger() -> logging.Logger:
    """Get or create the global logger."""
    global _logger
    if _logger is None:
        return setup_logger()
    return _logger


def log(msg: str, level: str = "INFO", tag: str = "SYSTEM") -> None:
    """Convenience logging function with tag support."""
    logger = get_logger()
    lvl = getattr(logging, level.upper(), logging.INFO)
    logger.log(lvl, msg, extra={"tag": tag})
