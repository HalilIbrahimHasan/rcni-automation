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
ENV_FILE = PROJECT_ROOT / ".env"
ENV_LOADED = load_dotenv(ENV_FILE)


class Config:
    """Application configuration sourced from environment variables."""

    GA_URL: str = os.getenv("GA_URL", "https://dummy-url.example.com")
    GA_EMAIL: str = os.getenv("GA_EMAIL", "dummy@example.com")
    GA_PASSWORD: str = os.getenv("GA_PASSWORD", "dummy_password")

    # HEADLESS=true → no visible browser | HEADLESS=false → visible browser
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
    def env_file_exists(cls) -> bool:
        """Return True if .env exists in the project root."""
        return ENV_FILE.exists()

    @classmethod
    def is_placeholder_config(cls) -> bool:
        """Return True if GA_URL or credentials are still dummy defaults."""
        return (
            "dummy" in cls.GA_URL.lower()
            or "dummy" in cls.GA_EMAIL.lower()
            or cls.GA_PASSWORD == "dummy_password"
        )

    @classmethod
    def log_startup_summary(cls, headless: bool) -> None:
        """Print a startup banner showing config source and browser mode."""
        from utils.logger import get_logger

        log = get_logger("config")
        browser_mode = "headless (invisible)" if headless else "headed (visible)"

        log.info("=" * 60)
        log.info("RCNI Framework startup")
        log.info("Project root : %s", PROJECT_ROOT)
        log.info(".env file   : %s", ENV_FILE if cls.env_file_exists() else "MISSING")
        log.info("GA_URL      : %s", cls.GA_URL)
        log.info("GA_EMAIL    : %s", cls.GA_EMAIL)
        log.info("Browser mode: %s", browser_mode)
        log.info("=" * 60)

        if not cls.env_file_exists():
            log.warning(
                "No .env file found. Create one: cp .env.example .env "
                "then add your credentials."
            )
        elif cls.is_placeholder_config():
            log.warning(
                "Credentials still look like placeholders. "
                "Update GA_URL, GA_EMAIL, and GA_PASSWORD in .env"
            )

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
