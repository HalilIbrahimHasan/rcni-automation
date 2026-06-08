"""
Video recording configuration for Playwright browser contexts.

Wraps context-level video options so conftest can enable or disable
recording based on environment settings.
"""

from typing import Optional

from utils.config import Config
from utils.logger import get_logger

logger = get_logger(__name__)


def get_video_context_options() -> Optional[dict]:
    """
    Return Playwright context options for video recording, or None if disabled.

    Use in conftest when creating the browser context fixture so
    videos are saved to reports/videos/ automatically on context close.

    Returns:
        Dict with record_video_dir and record_video_size, or None.
    """
    if not Config.VIDEO:
        logger.info("Video recording disabled")
        return None

    Config.ensure_report_dirs()
    logger.info("Video recording enabled → %s", Config.VIDEOS_DIR)

    return {
        "record_video_dir": str(Config.VIDEOS_DIR),
        "record_video_size": {"width": 1920, "height": 1080},
    }
