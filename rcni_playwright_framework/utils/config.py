"""
Central configuration loader for the RCNI Playwright framework.

Reads environment variables from .env via python-dotenv and exposes
typed, validated settings used across pages, fixtures, and utilities.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Project root is one level above utils/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


class Config:
    """Application configuration sourced from environment variables."""

    GA_URL: str = os.getenv("GA_URL", "https://dummy-url.example.com")
    GA_EMAIL: str = os.getenv("GA_EMAIL", "dummy@example.com")
    GA_PASSWORD: str = os.getenv("GA_PASSWORD", "dummy_password")

    HEADLESS: bool = os.getenv("HEADLESS", "false").lower() in ("true", "1", "yes")
    SLOW_MO: int = int(os.getenv("SLOW_MO", "200"))
    VIDEO: bool = os.getenv("VIDEO", "true").lower() in ("true", "1", "yes")
    TRACE: bool = os.getenv("TRACE", "true").lower() in ("true", "1", "yes")

    DEFAULT_TIMEOUT: int = int(os.getenv("DEFAULT_TIMEOUT", "60000"))
    NAVIGATION_TIMEOUT: int = int(os.getenv("NAVIGATION_TIMEOUT", "120000"))
    DOWNLOAD_TIMEOUT: int = int(os.getenv("DOWNLOAD_TIMEOUT", "3600000"))

    REPORTS_DIR: Path = PROJECT_ROOT / "reports"
    SCREENSHOTS_DIR: Path = REPORTS_DIR / "screenshots"
    VIDEOS_DIR: Path = REPORTS_DIR / "videos"
    TRACES_DIR: Path = REPORTS_DIR / "traces"
    HTML_DIR: Path = REPORTS_DIR / "html"
    FAILURES_DIR: Path = REPORTS_DIR / "failures"
    DOWNLOADS_DIR: Path = REPORTS_DIR / "downloads"

    TEST_DATA_DIR: Path = PROJECT_ROOT / "test_data"

    @classmethod
    def ensure_report_dirs(cls) -> None:
        """Create all report output directories if they do not exist."""
        for directory in (
            cls.SCREENSHOTS_DIR,
            cls.VIDEOS_DIR,
            cls.TRACES_DIR,
            cls.HTML_DIR,
            cls.FAILURES_DIR,
            cls.DOWNLOADS_DIR,
        ):
            directory.mkdir(parents=True, exist_ok=True)
