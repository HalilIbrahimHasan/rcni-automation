"""
Framework conftest — sys.path setup, CLI flags, and Playwright fixtures.

Launches Chrome/Edge/Chromium/Firefox/WebKit with robust headed-mode
arguments and automatic fallbacks when the primary browser fails.
"""

import sys
from pathlib import Path

# Must run before any pages/utils imports
_FRAMEWORK_ROOT = Path(__file__).resolve().parent
if str(_FRAMEWORK_ROOT) not in sys.path:
    sys.path.insert(0, str(_FRAMEWORK_ROOT))

# Playwright does not support Python 3.14+ yet — causes sync_playwright() timeout
if sys.version_info >= (3, 14):
    raise RuntimeError(
        f"Python {sys.version_info.major}.{sys.version_info.minor} is not supported. "
        "Playwright requires Python 3.11 or 3.12.\n"
        "Fix: install Python 3.12 from python.org, then recreate .venv:\n"
        "  py -3.12 -m venv .venv\n"
        "  .\\.venv\\Scripts\\activate\n"
        "  python -m pip install -r requirements.txt\n"
        "  python -m playwright install chromium"
    )

import pytest
from playwright.sync_api import sync_playwright

from utils.browser_utils import build_context_options, launch_browser, log_browser_config
from utils.config import Config
from utils.logger import get_logger
from utils.screenshot_utils import capture_failure_screenshot

logger = get_logger(__name__)

Config.ensure_report_dirs()
logger.info("=== Pytest session starting ===")


def pytest_sessionfinish(session, exitstatus):
    """Log final exit status — helps diagnose exit code -1 (process killed)."""
    status_map = {
        0: "PASSED (all tests ok)",
        1: "FAILED (test failures)",
        2: "INTERRUPTED (Ctrl+C)",
        3: "INTERNAL ERROR",
        4: "USAGE ERROR",
        5: "NO TESTS COLLECTED",
    }
    msg = status_map.get(exitstatus, f"UNKNOWN exit code {exitstatus}")
    logger.info("=== Pytest session finished: %s ===", msg)
    if exitstatus not in (0, 1):
        logger.warning(
            "Exit code %s often means the process was killed by the IDE, "
            "antivirus, or browser crash — check reports/last_run.log",
            exitstatus,
        )


def pytest_addoption(parser):
    """Register browser CLI flags."""
    group = parser.getgroup("rcni_browser", "RCNI browser launch options")
    group.addoption(
        "--headed",
        action="store_true",
        default=False,
        help="Visible browser window; overrides HEADLESS in .env",
    )
    group.addoption(
        "--headless",
        action="store_true",
        default=False,
        help="Headless browser; overrides HEADLESS in .env",
    )
    group.addoption(
        "--browser",
        action="store",
        default=None,
        choices=["chromium", "chrome", "msedge", "firefox", "webkit"],
        help="Browser to launch; overrides BROWSER in .env",
    )


def _resolve_headless(request) -> bool:
    """Determine headless mode from CLI flags or .env fallback."""
    if request.config.getoption("--headed", default=False):
        return False
    if request.config.getoption("--headless", default=False):
        return True
    return Config.HEADLESS


def _resolve_browser(request) -> str:
    """Determine browser from CLI flag or .env fallback."""
    cli_browser = request.config.getoption("--browser")
    if cli_browser:
        return cli_browser
    return Config.BROWSER


@pytest.fixture(scope="session")
def browser_launch_config(request):
    """
    Session-scoped browser launch settings resolved from CLI + .env.

    Returns dict with headless flag and browser name for fixtures.
    """
    headless = _resolve_headless(request)
    browser_name = _resolve_browser(request)

    Config.log_startup_summary(headless=headless)
    log_browser_config(headless=headless)
    logger.info("Resolved browser for session: %s", browser_name)

    return {"headless": headless, "browser": browser_name}


@pytest.fixture(scope="session")
def playwright_instance():
    """Start a Playwright session for the entire test run."""
    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture(scope="session")
def browser(playwright_instance, browser_launch_config):
    """
    Launch browser with Chrome args and automatic fallbacks.

    If installed Chrome fails, tries Edge then bundled Chromium.
    """
    headless = browser_launch_config["headless"]
    browser_name = browser_launch_config["browser"]
    logger.info("Starting browser launch (may try fallbacks if Chrome fails)...")
    try:
        browser = launch_browser(
            playwright_instance,
            headless=headless,
            browser_name=browser_name,
        )
        logger.info("Browser ready — tests can now run")
    except Exception as exc:
        logger.error("Browser launch failed completely: %s", exc)
        raise

    yield browser
    logger.info("Closing browser")
    browser.close()


@pytest.fixture
def context(browser, browser_launch_config, request):
    """Create a fresh browser context per test with optional tracing."""
    headless = browser_launch_config["headless"]
    context = browser.new_context(**build_context_options(headless))

    if Config.TRACE:
        context.tracing.start(screenshots=True, snapshots=True, sources=True)

    yield context

    if Config.TRACE:
        trace_path = Config.TRACES_DIR / f"{request.node.name}.zip"
        context.tracing.stop(path=str(trace_path))
        logger.info("Trace saved: %s", trace_path)

    context.close()


@pytest.fixture
def page(context, browser_launch_config):
    """Provide a fresh Page per test from the browser context."""
    page = context.new_page()
    page.set_default_timeout(Config.DEFAULT_TIMEOUT)
    page.set_default_navigation_timeout(Config.NAVIGATION_TIMEOUT)

    if not browser_launch_config["headless"]:
        try:
            page.bring_to_front()
        except Exception:
            pass

    yield page
    page.close()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Store test phase results on the item for failure screenshot hooks."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)


@pytest.fixture(autouse=True)
def screenshot_on_failure(request, page):
    """Capture a full-page failure screenshot when a test call phase fails."""
    yield

    rep = getattr(request.node, "rep_call", None)
    if rep and rep.failed:
        shot = capture_failure_screenshot(page, request.node.name)
        logger.error("Test failure screenshot: %s", shot)
