"""
GetInsured 834 download page object.

Handles portal login, dynamic folder-tree navigation by folder name,
pre-download screenshots, and file download with configurable timeout.
"""

from pathlib import Path
from typing import Optional

from playwright.sync_api import Page

from locators.download_locators import DownloadLocators as L
from pages.base_page import BasePage
from utils.config import Config
from utils.logger import get_logger
from utils.screenshot_utils import capture_screenshot
from utils.file_utils import get_download_path

logger = get_logger(__name__)


class GetInsured834DownloadPage(BasePage):
    """Page object for the GetInsured 834 folder download workflow."""

    def __init__(self, page: Page):
        """
        Initialise GetInsured834DownloadPage with the active browser page.

        Args:
            page: Playwright Page from the pytest fixture.
        """
        super().__init__(page)

    def login(
        self,
        url: str,
        email: str,
        password: str,
    ) -> None:
        """
        Log in to the GetInsured portal (separate from GA login).

        Use when the 834 download flow requires the GetInsured
        sign-in page with Username Or Email / Password fields.

        Args:
            url: GetInsured portal URL.
            email: Username or email credential.
            password: Account password.
        """
        logger.info("Logging in to GetInsured portal")
        self.page.goto(url, timeout=Config.NAVIGATION_TIMEOUT)

        self.safe_fill(
            self.resolve_by_role(L.USERNAME_ROLE, L.USERNAME_NAME),
            email,
            description="Username Or Email",
        )
        self.safe_fill(
            self.resolve_by_role(L.PASSWORD_ROLE, L.PASSWORD_NAME),
            password,
            description="Password",
        )
        self.safe_click(
            self.resolve_by_role(L.SIGN_IN_BUTTON_ROLE, L.SIGN_IN_BUTTON_NAME),
            description="Sign in button",
        )

        capture_screenshot(self.page, "getinsured_after_login")

    def _find_folder_row(self, folder_name: str):
        """
        Locate a folder table row by its visible name text.

        Uses name-based matching instead of nth-child indexing
        for resilient folder tree navigation.

        Args:
            folder_name: Visible folder name to match (case-insensitive).

        Returns:
            Playwright Locator for the matching table row.
        """
        rows = self.page.locator(L.FOLDER_ROW_CSS)
        count = rows.count()

        for index in range(count):
            row = rows.nth(index)
            name_cell = row.locator(L.FOLDER_NAME_CELL_CSS)
            try:
                text = name_cell.inner_text().strip().lower()
                if folder_name.lower() in text or text == folder_name.lower():
                    return row
            except Exception:
                continue

        raise ValueError(f"Folder '{folder_name}' not found in tree")

    def expand_folder(self, folder_name: str) -> None:
        """
        Expand a folder in the tree by clicking its chevron icon.

        Finds the row by folder name, then clicks the chevron
        to reveal child folders.

        Args:
            folder_name: Visible name of the folder to expand.
        """
        row = self._find_folder_row(folder_name)
        chevron = row.locator(L.FOLDER_CHEVRON_CSS)

        self.wait_for_visible(chevron, description=f"chevron for '{folder_name}'")
        self.safe_click(chevron, description=f"expand folder '{folder_name}'")
        logger.info("Expanded folder: %s", folder_name)

    def navigate_folder_path(self, folder_names: Optional[list[str]] = None) -> None:
        """
        Navigate through a sequence of folders by name.

        Replaces fragile nth-child navigation with dynamic
        name-based folder expansion.

        Args:
            folder_names: Ordered list of folder names to expand.
                          Defaults to L.DEFAULT_FOLDER_PATH.
        """
        path = folder_names or L.DEFAULT_FOLDER_PATH
        logger.info("Navigating folder path: %s", " → ".join(path))

        for folder_name in path:
            self.expand_folder(folder_name)

        capture_screenshot(self.page, "834_folder_navigated")

    def select_folder(self, folder_name: str) -> None:
        """
        Select a folder by clicking its checkbox cell.

        Args:
            folder_name: Visible name of the folder to select.
        """
        row = self._find_folder_row(folder_name)
        checkbox = row.locator(L.FOLDER_CHECKBOX_CSS)

        self.wait_for_visible(checkbox, description=f"checkbox for '{folder_name}'")
        self.safe_click(checkbox, description=f"select folder '{folder_name}'")
        logger.info("Selected folder: %s", folder_name)

    def download_folder(
        self,
        download_dir: Optional[Path] = None,
        timeout: Optional[int] = None,
    ) -> Path:
        """
        Click Download and save the file to reports/downloads/.

        Captures a pre-download screenshot and uses expect_download
        with a configurable timeout (default from Config.DOWNLOAD_TIMEOUT).

        Args:
            download_dir: Target directory; defaults to Config.DOWNLOADS_DIR.
            timeout: Download wait timeout in milliseconds.

        Returns:
            Path to the saved downloaded file.
        """
        download_dir = download_dir or Config.DOWNLOADS_DIR
        download_dir.mkdir(parents=True, exist_ok=True)
        timeout = timeout or Config.DOWNLOAD_TIMEOUT

        capture_screenshot(self.page, "834_before_download")

        download_link = self.resolve_by_role(L.DOWNLOAD_LINK_ROLE, L.DOWNLOAD_LINK_NAME)

        with self.page.expect_download(timeout=timeout) as download_info:
            self.safe_click(download_link, description="Download link")

        download = download_info.value
        target_path = get_download_path(download.suggested_filename)
        download.save_as(str(target_path))

        logger.info("Download saved: %s", target_path)
        return target_path

    def run_full_download_flow(
        self,
        url: str,
        email: str,
        password: str,
        folder_path: Optional[list[str]] = None,
        select_folder_name: str = "834",
    ) -> Path:
        """
        Execute the complete 834 download workflow end-to-end.

        Login → navigate folder tree → select target folder → download.

        Args:
            url: GetInsured portal URL.
            email: Login credential.
            password: Login password.
            folder_path: Ordered folder names to expand.
            select_folder_name: Final folder to select before download.

        Returns:
            Path to the downloaded file.
        """
        self.login(url, email, password)
        self.navigate_folder_path(folder_path)
        self.select_folder(select_folder_name)
        return self.download_folder()
