"""
RCNI report page object for results verification and data capture.

Handles waiting for report content, extracting table rows,
and capturing issuer-specific screenshots.
"""

from playwright.sync_api import Page

from locators.rcni_locators import RCNILocators as L
from pages.base_page import BasePage
from utils.config import Config
from utils.logger import get_logger
from utils.report_utils import extract_report_rows
from utils.screenshot_utils import capture_issuer_screenshots, capture_screenshot
from utils.wait_utils import wait_for_network_settled, wait_for_text

logger = get_logger(__name__)


class RCNIReportPage(BasePage):
    """Page object for RCNI reconciliation report results."""

    def __init__(self, page: Page):
        """
        Initialise RCNIReportPage with the active browser page.

        Args:
            page: Playwright Page from the pytest fixture.
        """
        super().__init__(page)

    def wait_for_report_content(self) -> None:
        """
        Wait for key report sections to render after a Go search.

        Attempts to detect 'TOP 5 DISCREPANCIES' and 'Issuer Activity'
        sections. Does not fail if sections are absent (no-report case).
        """
        for text in [L.TOP_DISCREPANCIES_TEXT, L.ISSUER_ACTIVITY_TEXT]:
            try:
                wait_for_text(self.page, text, timeout=Config.DEFAULT_TIMEOUT)
                logger.info("Report section visible: %s", text)
            except Exception:
                logger.warning("Report section not found: %s", text)

        try:
            wait_for_network_settled(self.page, timeout=Config.NAVIGATION_TIMEOUT)
        except Exception:
            logger.warning("Network idle wait timed out; continuing")

    def get_report_rows(self) -> list[dict[str, str]]:
        """
        Extract structured rows from the reconciliation results table.

        Call after wait_for_report_content() when results are expected.

        Returns:
            List of row dicts with file_name, status, report_name, etc.
        """
        return extract_report_rows(self.page)

    def capture_issuer_report(self, issuer_id: str) -> dict[str, str]:
        """
        Capture full-page and chart screenshots for an issuer report.

        Args:
            issuer_id: Issuer identifier for directory naming.

        Returns:
            Dict mapping screenshot label to file path.
        """
        capture_screenshot(self.page, f"issuer_{issuer_id}_full_page")
        return capture_issuer_screenshots(self.page, issuer_id)

    def has_results(self) -> bool:
        """
        Check whether at least one table row is present.

        Returns:
            True if table-row-0-cell-9 is visible.
        """
        try:
            first_row = self.resolve_by_test_id("table-row-0-cell-9")
            return first_row.is_visible()
        except Exception:
            return False
