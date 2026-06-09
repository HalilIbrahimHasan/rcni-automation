"""
Login page object for the Georgia Access portal.

Handles navigation to GA_URL, credential entry, and post-login
verification via the Enrollment menu item.
"""

from typing import Optional

from playwright.sync_api import Page

from locators.login_locators import LoginLocators as L
from pages.base_page import BasePage
from utils.config import Config
from utils.logger import get_logger
from utils.screenshot_utils import capture_screenshot

logger = get_logger(__name__)


class LoginPage(BasePage):
    """Page object for GA login and post-login landing verification."""

    def __init__(self, page: Page):
        """
        Initialise LoginPage with the active browser page.

        Args:
            page: Playwright Page from the pytest fixture.
        """
        super().__init__(page)

    def _email_locator(self):
        """Return the email input locator with role-first, CSS fallback."""
        return self.resolve_by_role(L.EMAIL_ROLE, L.EMAIL_NAME)

    def _password_locator(self):
        """Return the password input locator with role-first, CSS fallback."""
        return self.resolve_by_role(L.PASSWORD_ROLE, L.PASSWORD_NAME)

    def _login_button_locator(self):
        """Return the login button locator with role-first strategy."""
        return self.resolve_by_role(L.LOGIN_BUTTON_ROLE, L.LOGIN_BUTTON_NAME)

    def _enrollment_locator(self):
        """Return the post-login Enrollment menu locator."""
        return self.resolve_by_test_id(L.ENROLLMENT_TEST_ID)

    def goto(self, url: Optional[str] = None) -> None:
        """
        Navigate to the GA login URL and wait for the email field.

        Use as the first step in any test requiring authentication.
        Captures a login-page screenshot for audit trail.

        Args:
            url: Override URL; defaults to Config.GA_URL.
        """
        Config.require_ga_config()
        target_url = url or Config.GA_URL
        logger.info("STEP 1/3: Navigating to %s (timeout %ds)", target_url, Config.NAVIGATION_TIMEOUT // 1000)
        self.page.goto(
            target_url,
            timeout=Config.NAVIGATION_TIMEOUT,
            wait_until="domcontentloaded",
        )
        logger.info("STEP 1/3: Page loaded — waiting for email field")

        try:
            self.wait_for_visible(
                self._email_locator(),
                timeout=Config.NAVIGATION_TIMEOUT,
                description="Email Address field",
            )
        except Exception:
            logger.warning("Role locator failed for email; trying CSS fallback")
            self.wait_for_visible(
                self.resolve_by_css(L.EMAIL_CSS),
                description="Email Address field (CSS fallback)",
            )

        capture_screenshot(self.page, "login_page")

    def login(
        self,
        email: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        """
        Fill credentials, submit the form, and verify login success.

        Waits for the Enrollment menu as the login-success indicator.
        Captures a post-login screenshot after verification.

        Args:
            email: Login email; defaults to Config.GA_EMAIL.
            password: Login password; defaults to Config.GA_PASSWORD.
        """
        email = email or Config.GA_EMAIL
        password = password or Config.GA_PASSWORD

        logger.info("STEP 2/3: Logging in as %s", email)

        self.safe_fill(self._email_locator(), email, description="Email Address")
        self.safe_fill(self._password_locator(), password, description="Password")
        self.safe_click(self._login_button_locator(), description="Login button")
        logger.info("STEP 3/3: Waiting for Enrollment menu (login success)")

        enrollment = self._enrollment_locator()
        self.wait_for_visible(
            enrollment,
            timeout=Config.NAVIGATION_TIMEOUT,
            description="Enrollment menu (login success)",
        )
        self.assert_visible(enrollment, description="Enrollment menu")

        capture_screenshot(self.page, "after_login")
        logger.info("Login successful")

    def is_logged_in(self) -> bool:
        """
        Check whether the Enrollment menu is visible (logged-in state).

        Use for soft checks without raising exceptions.

        Returns:
            True if Enrollment is visible, False otherwise.
        """
        try:
            return self._enrollment_locator().is_visible()
        except Exception:
            return False
