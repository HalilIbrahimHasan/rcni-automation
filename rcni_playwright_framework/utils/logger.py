"""
Structured logging utility for the RCNI Playwright framework.

Provides a consistent logger instance so pages, tests, and utilities
emit uniform, timestamped messages during automation runs.
"""

import logging
import sys


def get_logger(name: str = "rcni_framework") -> logging.Logger:
    """
    Return a configured logger for the given module or component name.

    Use this in page objects and utilities instead of bare print()
    so log output is consistent and filterable.

    Args:
        name: Logger name, typically __name__ of the calling module.

    Returns:
        A logging.Logger instance with stream handler attached.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    return logger
