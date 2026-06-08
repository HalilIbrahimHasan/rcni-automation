"""
Screenshot capture helpers for the RCNI Playwright framework.

Provides named, timestamped full-page captures at key workflow stages
and dedicated failure artifact storage.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from playwright.sync_api import Page

from utils.config import Config
from utils.logger import get_logger

logger = get_logger(__name__)


def _timestamp() -> str:
    """Return a filesystem-safe timestamp string for file naming."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def capture_screenshot(
    page: Page,
    name: str,
    directory: Optional[Path] = None,
    full_page: bool = True,
) -> str:
    """
    Capture a screenshot and return its absolute path as a string.

    Use at workflow milestones: login, post-login, RCNI landing,
    after filter search, and per-issuer report views.

    Args:
        page: Active Playwright Page.
        name: Base name for the file (spaces replaced with underscores).
        directory: Target folder; defaults to Config.SCREENSHOTS_DIR.
        full_page: Whether to capture the entire scrollable page.

    Returns:
        String path to the saved screenshot file.
    """
    Config.ensure_report_dirs()
    directory = directory or Config.SCREENSHOTS_DIR
    directory.mkdir(parents=True, exist_ok=True)

    safe_name = name.replace(" ", "_").replace("/", "-")
    filepath = directory / f"{safe_name}_{_timestamp()}.png"
    page.screenshot(path=str(filepath), full_page=full_page)
    logger.info("Screenshot saved: %s", filepath)
    return str(filepath)


def capture_failure_screenshot(
    page: Page,
    test_name: str,
    suffix: str = "",
) -> str:
    """
    Capture a failure screenshot into the failures report directory.

    Use from conftest hooks or page object error handlers when
    a test or issuer iteration fails.

    Args:
        page: Active Playwright Page.
        test_name: Pytest node name or issuer identifier.
        suffix: Optional extra label appended to the filename.

    Returns:
        String path to the saved failure screenshot.
    """
    Config.ensure_report_dirs()
    label = f"{test_name}_{suffix}" if suffix else test_name
    safe_label = label.replace(" ", "_").replace("/", "-")
    filepath = Config.FAILURES_DIR / f"{safe_label}_{_timestamp()}.png"
    page.screenshot(path=str(filepath), full_page=True)
    logger.error("Failure screenshot saved: %s", filepath)
    return str(filepath)


def capture_issuer_screenshots(page: Page, issuer_id: str) -> dict:
    """
    Capture a standard set of issuer report screenshots.

    Mirrors the legacy capture flow: main view, chart sections,
    and full-page report. Used during issuer report capture tests.

    Args:
        page: Active Playwright Page on the RCNI report view.
        issuer_id: Issuer identifier used for directory naming.

    Returns:
        Dict mapping screenshot label to file path.
    """
    issuer_dir = Config.SCREENSHOTS_DIR / issuer_id
    issuer_dir.mkdir(parents=True, exist_ok=True)

    screenshots = {}

    screenshots["Full Page Report"] = capture_screenshot(
        page, "full_page_report", directory=issuer_dir
    )

    for label, selector in [
        ("Main Chart", ".css-15rufqy"),
        ("Secondary Chart", ".css-h1sary"),
    ]:
        try:
            locator = page.locator(selector).first
            if locator.is_visible():
                path = issuer_dir / f"{label.replace(' ', '_')}_{_timestamp()}.png"
                locator.screenshot(path=str(path))
                screenshots[label] = str(path)
        except Exception as exc:
            logger.warning("Could not capture %s for issuer %s: %s", label, issuer_id, exc)

    return screenshots
