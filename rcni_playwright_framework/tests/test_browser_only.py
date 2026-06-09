"""
Minimal browser diagnostic — finishes in under 30 seconds.

Run this FIRST to confirm Playwright can open a browser on your machine.
Does not use GA_URL or credentials.
"""

import pytest

from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
def test_browser_opens_and_loads_page(page):
    """
    Open a blank page and verify the browser responds.

    If this passes, Playwright works — any hang is in login/RCNI steps.
    """
    logger.info("DIAGNOSTIC: opening https://www.google.com")
    page.goto("https://www.google.com", timeout=30000, wait_until="domcontentloaded")
    assert "google" in page.url.lower()
    logger.info("DIAGNOSTIC: browser opened google.com — url=%s", page.url)
