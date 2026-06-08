"""
Base page object with shared Playwright interaction helpers.

All page classes inherit from BasePage to get retry-friendly
click, fill, dropdown, wait, and failure-artifact methods.
"""

from pathlib import Path
from typing import Optional, Union

from playwright.sync_api import Locator, Page, expect

from utils.config import Config
from utils.logger import get_logger
from utils.screenshot_utils import capture_failure_screenshot
from utils.wait_utils import wait_for_url_or_element, wait_for_visible

logger = get_logger(__name__)


class BasePage:
    """Foundation page object providing resilient Playwright helpers."""

    def __init__(self, page: Page):
        """
        Initialise the page object with an active Playwright Page.

        Args:
            page: Browser page instance from the pytest fixture.
        """
        self.page = page
        self.default_timeout = Config.DEFAULT_TIMEOUT

    def resolve_by_test_id(self, test_id: str) -> Locator:
        """
        Return a locator for a data-testid attribute.

        Preferred locator strategy — use when the application
        exposes stable test identifiers.

        Args:
            test_id: Value of the data-testid attribute.

        Returns:
            Playwright Locator for the element.
        """
        return self.page.get_by_test_id(test_id)

    def resolve_by_role(self, role: str, name: str) -> Locator:
        """
        Return a role-based locator with an accessible name.

        Second-priority strategy after data-testid.

        Args:
            role: ARIA role string (e.g. 'button', 'textbox', 'link').
            name: Accessible name of the element.

        Returns:
            Playwright Locator for the element.
        """
        return self.page.get_by_role(role, name=name)

    def resolve_by_text(self, text: str, exact: bool = False) -> Locator:
        """
        Return a text-based locator.

        Third-priority strategy for elements without testid or role.

        Args:
            text: Visible text to match.
            exact: Whether to require an exact text match.

        Returns:
            Playwright Locator for the element.
        """
        return self.page.get_by_text(text, exact=exact)

    def resolve_by_css(self, selector: str) -> Locator:
        """
        Return a CSS selector locator as a last-resort fallback.

        Args:
            selector: CSS selector string.

        Returns:
            Playwright Locator for the element.
        """
        return self.page.locator(selector)

    def wait_for_visible(
        self,
        locator: Locator,
        timeout: Optional[int] = None,
        description: str = "element",
    ) -> Locator:
        """
        Wait until a locator is visible before interacting.

        Delegates to wait_utils.wait_for_visible for consistency.

        Args:
            locator: Target Playwright Locator.
            timeout: Optional override timeout in milliseconds.
            description: Label for logging.

        Returns:
            The visible Locator.
        """
        return wait_for_visible(locator, timeout=timeout, description=description)

    def wait_for_url_or_element(
        self,
        url_pattern: Optional[str] = None,
        locator: Optional[Locator] = None,
        timeout: Optional[int] = None,
    ) -> None:
        """
        Wait for navigation to complete via URL or landmark element.

        Use after login or menu clicks when the next view is
        confirmed by either URL change or a known element.

        Args:
            url_pattern: Regex or substring for expected URL.
            locator: Landmark element signalling page readiness.
            timeout: Optional override timeout in milliseconds.
        """
        wait_for_url_or_element(
            self.page,
            url_pattern=url_pattern,
            locator=locator,
            timeout=timeout,
        )

    def safe_click(
        self,
        locator: Locator,
        timeout: Optional[int] = None,
        description: str = "element",
        retries: int = 2,
    ) -> None:
        """
        Click an element with visibility wait and limited retries.

        Use for all interactive clicks instead of bare .click() to
        handle slow renders and transient overlay blocks.

        Args:
            locator: Target Playwright Locator.
            timeout: Per-attempt timeout in milliseconds.
            description: Label for logging.
            retries: Number of retry attempts on failure.

        Raises:
            Exception: Re-raises the last error if all retries fail.
        """
        timeout = timeout or self.default_timeout
        last_error = None

        for attempt in range(1, retries + 2):
            try:
                self.wait_for_visible(locator, timeout=timeout, description=description)
                locator.click()
                logger.info("Clicked: %s", description)
                return
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Click attempt %d failed for %s: %s", attempt, description, exc
                )

        raise last_error

    def safe_fill(
        self,
        locator: Locator,
        value: str,
        timeout: Optional[int] = None,
        description: str = "input",
        retries: int = 2,
    ) -> None:
        """
        Fill an input field with visibility wait and limited retries.

        Use for email, password, and search fields.

        Args:
            locator: Target input Locator.
            value: Text value to enter.
            timeout: Per-attempt timeout in milliseconds.
            description: Label for logging.
            retries: Number of retry attempts on failure.

        Raises:
            Exception: Re-raises the last error if all retries fail.
        """
        timeout = timeout or self.default_timeout
        last_error = None

        for attempt in range(1, retries + 2):
            try:
                self.wait_for_visible(locator, timeout=timeout, description=description)
                locator.fill(value)
                logger.info("Filled: %s", description)
                return
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "Fill attempt %d failed for %s: %s", attempt, description, exc
                )

        raise last_error

    def safe_select_dropdown(
        self,
        locator: Locator,
        value: str,
        label: Optional[str] = None,
        timeout: Optional[int] = None,
        description: str = "dropdown",
    ) -> None:
        """
        Select a dropdown option by value with role-based fallback.

        Tries native select_option first; falls back to click + option
        role when the element is a custom dropdown component.

        Args:
            locator: Dropdown Locator (native or custom).
            value: Option value attribute to select.
            label: Optional visible label for custom dropdown fallback.
            timeout: Wait timeout in milliseconds.
            description: Label for logging.
        """
        timeout = timeout or self.default_timeout
        self.wait_for_visible(locator, timeout=timeout, description=description)

        try:
            locator.select_option(value)
            logger.info("Selected option value=%s in %s", value, description)
        except Exception:
            locator.click()
            option_label = label or value
            option = self.page.get_by_role("option", name=option_label)
            self.safe_click(option, description=f"option '{option_label}'")

    def capture_failure_artifacts(
        self,
        test_name: str,
        suffix: str = "",
    ) -> dict[str, str]:
        """
        Capture screenshot and optional trace path on failure.

        Use in test exception handlers or conftest failure hooks
        to preserve debugging context.

        Args:
            test_name: Pytest node name or issuer identifier.
            suffix: Optional extra label for the artifact filename.

        Returns:
            Dict with 'screenshot' path and any other artifact paths.
        """
        artifacts = {
            "screenshot": capture_failure_screenshot(self.page, test_name, suffix=suffix),
        }
        logger.error("Failure artifacts captured for %s", test_name)
        return artifacts

    def assert_visible(self, locator: Locator, description: str = "element") -> None:
        """
        Assert that an element is visible on the page.

        Args:
            locator: Target Locator to assert.
            description: Label for logging.
        """
        expect(locator).to_be_visible()
        logger.info("Verified visible: %s", description)
