"""
RCNI dashboard page object for navigation and filter selection.

Handles Enrollment → Reconciliation Workbench navigation and
issuer/month/year dropdown interactions.
"""

from typing import Optional

from playwright.sync_api import Page

from locators.rcni_locators import RCNILocators as L
from pages.base_page import BasePage
from utils.config import Config
from utils.logger import get_logger
from utils.screenshot_utils import capture_screenshot

logger = get_logger(__name__)


class RCNIDashboardPage(BasePage):
    """Page object for RCNI navigation and reconciliation filter controls."""

    def __init__(self, page: Page):
        """
        Initialise RCNIDashboardPage with the active browser page.

        Args:
            page: Playwright Page from the pytest fixture.
        """
        super().__init__(page)

    def navigate_to_reconciliation(self) -> None:
        """
        Click Enrollment then open Reconciliation Workbench End.

        Use after login to reach the RCNI filter panel. Waits for
        all three filter dropdowns before returning.
        """
        logger.info("Navigating to Reconciliation Workbench")

        enrollment = self.resolve_by_test_id(L.ENROLLMENT_TEST_ID)
        self.safe_click(enrollment, description="Enrollment menu")

        rcni_link = self.resolve_by_role(
            L.RECONCILIATION_LINK_ROLE,
            L.RECONCILIATION_LINK_NAME,
        )
        self.wait_for_visible(
            rcni_link,
            timeout=Config.NAVIGATION_TIMEOUT,
            description="Reconciliation Workbench link",
        )
        self.safe_click(rcni_link, description="Reconciliation Workbench End")

        self._wait_for_filter_panel()
        capture_screenshot(self.page, "rcni_landing_page")
        logger.info("RCNI dashboard loaded")

    def _wait_for_filter_panel(self) -> None:
        """
        Wait until issuer, month, and year dropdowns are visible.

        Internal helper called after navigation to ensure the
        filter panel is ready for interaction.
        """
        for test_id, label in [
            (L.MONTH_DROPDOWN_TEST_ID, "Month dropdown"),
            (L.ISSUER_DROPDOWN_TEST_ID, "Issuer dropdown"),
            (L.YEAR_DROPDOWN_TEST_ID, "Year dropdown"),
        ]:
            self.wait_for_visible(
                self.resolve_by_test_id(test_id),
                timeout=Config.NAVIGATION_TIMEOUT,
                description=label,
            )

    def select_month(self, value: str, label: Optional[str] = None) -> None:
        """
        Select the reconciliation month dropdown value.

        Args:
            value: Option value (e.g. '5' for May).
            label: Visible label fallback (e.g. 'May').
        """
        dropdown = self.resolve_by_test_id(L.MONTH_DROPDOWN_TEST_ID)
        self.safe_select_dropdown(
            dropdown,
            value=value,
            label=label,
            description="Reconciliation month",
        )

    def select_issuer(self, issuer_id: str) -> str:
        """
        Select an issuer from the dropdown and return its display name.

        Args:
            issuer_id: Issuer ID value to select.

        Returns:
            Display name of the selected issuer.
        """
        dropdown = self.resolve_by_test_id(L.ISSUER_DROPDOWN_TEST_ID)
        self.safe_select_dropdown(
            dropdown,
            value=issuer_id,
            label=issuer_id,
            description=f"Issuer {issuer_id}",
        )

        try:
            issuer_name = dropdown.evaluate(
                """
                el => el.options
                    ? el.options[el.selectedIndex].textContent.trim()
                    : el.innerText.trim()
                """
            )
        except Exception:
            issuer_name = issuer_id

        logger.info("Selected issuer: %s (%s)", issuer_name, issuer_id)
        return issuer_name

    def select_year(self, value: str, label: Optional[str] = None) -> None:
        """
        Select the reconciliation year dropdown value.

        Args:
            value: Option value (e.g. '2025').
            label: Visible label fallback (e.g. '2025').
        """
        dropdown = self.resolve_by_test_id(L.YEAR_DROPDOWN_TEST_ID)
        self.safe_select_dropdown(
            dropdown,
            value=value,
            label=label,
            description="Reconciliation year",
        )

    def click_go(self) -> None:
        """
        Click the reconciliation Go button to run the search.

        Use after all three filters (month, issuer, year) are set.
        """
        go_button = self.resolve_by_test_id(L.GO_BUTTON_TEST_ID)
        self.safe_click(go_button, description="Reconciliation Go button")

    def apply_filters(
        self,
        issuer_id: str,
        month: str,
        year: str,
        month_label: Optional[str] = None,
    ) -> str:
        """
        Set month, issuer, and year filters then click Go.

        Convenience method that combines the three dropdown selections
        and triggers the search in one call.

        Args:
            issuer_id: Issuer ID to select.
            month: Month option value.
            year: Year option value.
            month_label: Optional month display label.

        Returns:
            Display name of the selected issuer.
        """
        self.select_month(month, label=month_label)
        issuer_name = self.select_issuer(issuer_id)
        self.select_year(year, label=year)
        self.click_go()
        capture_screenshot(
            self.page,
            f"after_search_{issuer_id}_{month}_{year}",
        )
        return issuer_name

    def return_to_dashboard(self) -> None:
        """
        Navigate back to the RCNI filter panel from a report view.

        Use between issuer iterations to reset the filter panel
        without re-logging in.
        """
        try:
            self.navigate_to_reconciliation()
        except Exception as exc:
            logger.warning("Could not return to RCNI dashboard: %s", exc)
