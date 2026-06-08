"""
Root conftest — registers CLI flags so pytest finds them even when
the workspace root is 'rcni automation' instead of rcni_playwright_framework.
"""


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
