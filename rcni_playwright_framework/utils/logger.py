"""
Structured logging utility for the RCNI Playwright framework.

Logs to console AND reports/last_run.log so output survives IDE kills
(exit code -1) when the terminal buffer is cleared.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

_LOG_FILE: Optional[Path] = None
_FILE_HANDLER_ADDED = False


def get_log_file_path() -> Path:
    """Return path to the persistent session log file."""
    global _LOG_FILE
    if _LOG_FILE is None:
        from utils.config import Config

        Config.ensure_report_dirs()
        _LOG_FILE = Config.REPORTS_DIR / "last_run.log"
    return _LOG_FILE


def _ensure_file_handler() -> None:
    """Attach one shared file handler to the root logger."""
    global _FILE_HANDLER_ADDED
    if _FILE_HANDLER_ADDED:
        return

    log_path = get_log_file_path()
    # Fresh log each run
    log_path.write_text("", encoding="utf-8")

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.INFO)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    if not root.handlers:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        root.addHandler(stream_handler)
    root.addHandler(file_handler)

    _FILE_HANDLER_ADDED = True
    root.info("Session log file: %s", log_path)


def get_logger(name: str = "rcni_framework") -> logging.Logger:
    """
    Return a configured logger for the given module or component name.

    Use this in page objects and utilities instead of bare print()
    so log output is consistent and filterable.
    """
    _ensure_file_handler()
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    return logger
