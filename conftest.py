"""
Workspace-root conftest — registers CLI flags and Playwright fixtures
when pytest is run from the parent 'rcni automation' folder.
"""

import sys
from pathlib import Path

_FRAMEWORK_ROOT = Path(__file__).resolve().parent / "rcni_playwright_framework"
if str(_FRAMEWORK_ROOT) not in sys.path:
    sys.path.insert(0, str(_FRAMEWORK_ROOT))


def pytest_addoption(parser):
    """Register --headed / --headless browser flags for all test runs."""
    group = parser.getgroup("rcni_browser", "RCNI browser launch options")
    group.addoption(
        "--headed",
        action="store_true",
        default=False,
        help="Run browser in headed (visible) mode; overrides HEADLESS in .env",
    )
    group.addoption(
        "--headless",
        action="store_true",
        default=False,
        help="Run browser in headless mode; overrides HEADLESS in .env",
    )
