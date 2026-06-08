"""
Smoke tests for GA login and RCNI dashboard navigation.

Verifies authentication and navigation to the Reconciliation
Workbench without running the full issuer report loop.
"""

import pytest

from pages.login_page import LoginPage
from pages.rcni_dashboard_page import RCNIDashboardPage
from utils.config import Config
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.smoke
@pytest.mark.rcni
def test_login_and_navigate_to_rcni(page):
    """
    Log in to GA and navigate to the RCNI Reconciliation Workbench.

    Confirms the Enrollment menu appears after login and that
    the issuer/month/year filter panel loads on the RCNI page.
    """
    login_page = LoginPage(page)
    login_page.goto()
    login_page.login()

    assert login_page.is_logged_in(), "Expected Enrollment menu after login"

    dashboard = RCNIDashboardPage(page)
    dashboard.navigate_to_reconciliation()

    issuer_dropdown = dashboard.resolve_by_test_id("issuerName")
    dashboard.wait_for_visible(issuer_dropdown, description="Issuer dropdown")
    dashboard.assert_visible(issuer_dropdown, description="Issuer dropdown")

    logger.info("Login and RCNI navigation successful")


@pytest.mark.smoke
@pytest.mark.rcni
def test_login_page_loads(page):
    """
    Verify the login page renders the email input field.

    Lightweight smoke check that does not submit credentials.
    """
    login_page = LoginPage(page)
    login_page.goto()

    email_field = login_page.resolve_by_role("textbox", "Email Address")
    login_page.assert_visible(email_field, description="Email Address field")

    logger.info("Login page loaded at %s", Config.GA_URL)
