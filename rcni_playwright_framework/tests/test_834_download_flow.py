"""
Tests for the GetInsured 834 folder download workflow.

Covers dynamic folder navigation, pre-download screenshots,
and file download with configurable timeout.
"""

import os

import pytest

from pages.getinsured_834_download_page import GetInsured834DownloadPage
from utils.config import Config
from utils.logger import get_logger

logger = get_logger(__name__)


@pytest.mark.download
@pytest.mark.regression
def test_834_download_flow(page):
    """
    Execute the full 834 download workflow on the GetInsured portal.

    Logs in, navigates the folder tree by name, selects the 834
    folder, and saves the download to reports/downloads/.
    """
    download_page = GetInsured834DownloadPage(page)

    gi_url = os.getenv("GI_URL", Config.GA_URL)
    gi_email = os.getenv("GI_EMAIL", Config.GA_EMAIL)
    gi_password = os.getenv("GI_PASSWORD", Config.GA_PASSWORD)

    downloaded_path = download_page.run_full_download_flow(
        url=gi_url,
        email=gi_email,
        password=gi_password,
        folder_path=["archive", "in", "good"],
        select_folder_name="834",
    )

    assert downloaded_path.exists(), f"Download file not found: {downloaded_path}"
    logger.info("834 download completed: %s", downloaded_path)


@pytest.mark.download
@pytest.mark.smoke
def test_834_folder_navigation(page):
    """
    Smoke test: verify dynamic folder navigation by name works.

    Logs in and expands the default folder path without downloading.
    """
    download_page = GetInsured834DownloadPage(page)

    gi_url = os.getenv("GI_URL", Config.GA_URL)
    gi_email = os.getenv("GI_EMAIL", Config.GA_EMAIL)
    gi_password = os.getenv("GI_PASSWORD", Config.GA_PASSWORD)

    download_page.login(gi_url, gi_email, gi_password)
    download_page.navigate_folder_path(["archive", "in", "good"])

    logger.info("834 folder navigation smoke test complete")
