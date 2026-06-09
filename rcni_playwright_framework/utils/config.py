"""
Central configuration loader for the RCNI Playwright framework.

Reads environment variables from .env via python-dotenv and exposes
typed, validated settings used across pages, fixtures, and utilities.

Install:  pip install python-dotenv   (NOT pip install dotenv)
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

    # No hardcoded dummy values — must come from .env
    GA_URL: str = os.getenv("GA_URL", "").strip()
    GA_EMAIL: str = os.getenv("GA_EMAIL", "").strip()
    GA_PASSWORD: str = os.getenv("GA_PASSWORD", "").strip()

    # HEADLESS=true → no visible browser | HEADLESS=false → visible browser
    HEADLESS: bool = os.getenv("HEADLESS", "false").lower() in ("true", "1", "yes")
    SLOW_MO: int = int(os.getenv("SLOW_MO", "0"))
    VIDEO: bool = os.getenv("VIDEO", "false").lower() in ("true", "1", "yes")
    TRACE: bool = os.getenv("TRACE", "false").lower() in ("true", "1", "yes")

    # Browser: chromium (default, no Chrome install needed) | chrome | msedge | firefox | webkit
    BROWSER: str = os.getenv("BROWSER", "chromium").lower().strip()
    BROWSER_CHANNEL: str = os.getenv("BROWSER_CHANNEL", "").strip()
    BROWSER_EXECUTABLE: str = os.getenv("BROWSER_EXECUTABLE", "").strip()
    BROWSER_EXTRA_ARGS: str = os.getenv("BROWSER_EXTRA_ARGS", "")
    BROWSER_STABILITY_ARGS: bool = os.getenv(
        "BROWSER_STABILITY_ARGS", "true"
    ).lower() in ("true", "1", "yes")
    BROWSER_FALLBACK: bool = os.getenv("BROWSER_FALLBACK", "false").lower() in (
        "true", "1", "yes",
    )

    DEFAULT_TIMEOUT: int = int(os.getenv("DEFAULT_TIMEOUT", "20000"))
    NAVIGATION_TIMEOUT: int = int(os.getenv("NAVIGATION_TIMEOUT", "60000"))
    REPORT_WAIT_TIMEOUT: int = int(os.getenv("REPORT_WAIT_TIMEOUT", "15000"))
    BROWSER_LAUNCH_TIMEOUT: int = int(os.getenv("BROWSER_LAUNCH_TIMEOUT", "30000"))
    TEST_TIMEOUT: int = int(os.getenv("TEST_TIMEOUT", "300"))
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
    def is_ga_configured(cls) -> bool:
        """Return True if GA_URL, GA_EMAIL, and GA_PASSWORD are all set in .env."""
        return bool(cls.GA_URL and cls.GA_EMAIL and cls.GA_PASSWORD)

    @classmethod
    def require_ga_config(cls) -> None:
        """
        Raise a clear error if GA credentials are missing.

        Call at the start of login/RCNI tests (not browser-only tests).
        """
        missing = []
        if not cls.GA_URL:
            missing.append("GA_URL")
        if not cls.GA_EMAIL:
            missing.append("GA_EMAIL")
        if not cls.GA_PASSWORD:
            missing.append("GA_PASSWORD")

        if not cls.env_file_exists():
            raise RuntimeError(
                f".env file not found at {ENV_FILE}\n"
                "Create it: copy .env.example to .env and add your credentials."
            )

        if missing:
            raise RuntimeError(
                f"Missing required values in .env: {', '.join(missing)}\n"
                f"Edit: {ENV_FILE}"
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
        log.info("GA_URL      : %s", cls.GA_URL or "(not set)")
        log.info("GA_EMAIL    : %s", cls.GA_EMAIL or "(not set)")
        log.info("Browser     : %s", cls.BROWSER)
        log.info("Browser mode: %s", browser_mode)
        log.info("=" * 60)

        if not cls.env_file_exists():
            log.warning(
                "No .env file found. Create one: copy .env.example to .env "
                "then add your credentials."
            )
        elif not cls.is_ga_configured():
            log.warning(
                "GA_URL / GA_EMAIL / GA_PASSWORD not set in .env — "
                "login tests will fail until you add them."
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
