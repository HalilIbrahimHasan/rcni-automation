"""
File system helpers for reports, downloads, and test artifacts.

Provides safe directory creation and path resolution used by
screenshot, download, and HTML report utilities.
"""

from pathlib import Path
from typing import Union

from utils.config import Config
from utils.logger import get_logger

logger = get_logger(__name__)


def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Create a directory (and parents) if it does not exist.

    Use before writing screenshots, downloads, or HTML reports.

    Args:
        path: Target directory path.

    Returns:
        Resolved Path object.
    """
    resolved = Path(path)
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def get_issuer_report_dir(issuer_id: str) -> Path:
    """
    Return the screenshot directory for a specific issuer.

    Use when storing per-issuer artifacts under reports/screenshots/.

    Args:
        issuer_id: Issuer identifier string.

    Returns:
        Path to the issuer-specific screenshot folder.
    """
    issuer_dir = Config.SCREENSHOTS_DIR / issuer_id
    return ensure_directory(issuer_dir)


def get_download_path(filename: str) -> Path:
    """
    Resolve the full path for a downloaded file in reports/downloads/.

    Use with Playwright expect_download save_as targets.

    Args:
        filename: Suggested or custom filename for the download.

    Returns:
        Full Path where the file should be saved.
    """
    return ensure_directory(Config.DOWNLOADS_DIR) / filename
