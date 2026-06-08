"""
Dynamic wait helpers for Playwright interactions.

Centralises visibility, URL, and element-state waits so page objects
avoid hard-coded sleep calls and use retry-friendly polling instead.
"""

import re
from typing import Optional, Union

from playwright.sync_api import Locator, Page, expect

from utils.config import Config
from utils.logger import get_logger

logger = get_logger(__name__)


def wait_for_visible(
    locator: Locator,
    timeout: Optional[int] = None,
    description: str = "element",
) -> Locator:
    """
    Wait until a locator is visible and return it for chaining.

    Use before clicks, fills, or assertions when an element may
    render asynchronously after navigation or AJAX updates.

    Args:
        locator: Playwright Locator to wait on.
        timeout: Max wait in milliseconds; defaults to Config.DEFAULT_TIMEOUT.
        description: Human-readable label for log messages.

    Returns:
        The same Locator after it becomes visible.
    """
    timeout = timeout or Config.DEFAULT_TIMEOUT
    logger.info("Waiting for visible: %s", description)
    locator.wait_for(state="visible", timeout=timeout)
    return locator


def wait_for_hidden(
    locator: Locator,
    timeout: Optional[int] = None,
    description: str = "element",
) -> Locator:
    """
    Wait until a locator is hidden or detached from the DOM.

    Use after form submissions or modal dismissals when you need
    to confirm a loading overlay or dialog has disappeared.

    Args:
        locator: Playwright Locator to wait on.
        timeout: Max wait in milliseconds.
        description: Human-readable label for log messages.

    Returns:
        The same Locator after it becomes hidden.
    """
    timeout = timeout or Config.DEFAULT_TIMEOUT
    logger.info("Waiting for hidden: %s", description)
    locator.wait_for(state="hidden", timeout=timeout)
    return locator


def wait_for_url_or_element(
    page: Page,
    url_pattern: Optional[Union[str, re.Pattern]] = None,
    locator: Optional[Locator] = None,
    timeout: Optional[int] = None,
) -> None:
    """
    Wait for either a URL change or a target element to appear.

    Use after login or navigation when the next page may be identified
    by URL fragment or by a landmark element such as a menu item.

    Args:
        page: Active Playwright Page.
        url_pattern: Regex or substring to match against page.url.
        locator: Optional Locator that signals navigation success.
        timeout: Max wait in milliseconds.

    Raises:
        TimeoutError: If neither condition is met within the timeout.
    """
    timeout = timeout or Config.NAVIGATION_TIMEOUT
    logger.info("Waiting for URL pattern=%s or locator", url_pattern)

    if locator is not None:
        try:
            locator.wait_for(state="visible", timeout=timeout)
            return
        except Exception:
            if url_pattern is None:
                raise

    if url_pattern is not None:
        page.wait_for_url(url_pattern, timeout=timeout)


def wait_for_network_settled(page: Page, timeout: Optional[int] = None) -> None:
    """
    Wait for the page network activity to reach an idle state.

    Use sparingly after heavy data loads (e.g. RCNI report tables)
    when element-based waits alone are insufficient.

    Args:
        page: Active Playwright Page.
        timeout: Max wait in milliseconds.
    """
    timeout = timeout or Config.NAVIGATION_TIMEOUT
    logger.info("Waiting for network idle")
    page.wait_for_load_state("networkidle", timeout=timeout)


def wait_for_text(
    page: Page,
    text: str,
    timeout: Optional[int] = None,
    exact: bool = False,
) -> Locator:
    """
    Wait until visible text appears on the page.

    Use to confirm report sections such as 'TOP 5 DISCREPANCIES'
    or 'Issuer Activity' have rendered after a search.

    Args:
        page: Active Playwright Page.
        text: Text string to locate.
        timeout: Max wait in milliseconds.
        exact: Whether to match the full string exactly.

    Returns:
        The Locator matching the text.
    """
    timeout = timeout or Config.DEFAULT_TIMEOUT
    locator = page.get_by_text(text, exact=exact)
    locator.wait_for(state="visible", timeout=timeout)
    return locator


def assert_visible(locator: Locator, description: str = "element") -> None:
    """
    Assert that a locator is visible using Playwright expect.

    Use in page objects at verification checkpoints.

    Args:
        locator: Playwright Locator to assert.
        description: Human-readable label for log messages.
    """
    logger.info("Asserting visible: %s", description)
    expect(locator).to_be_visible()
