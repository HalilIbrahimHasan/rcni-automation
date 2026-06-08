"""
Shared Playwright pytest fixtures for the RCNI framework.

Imported by conftest.py at both the workspace root and framework root
so the page/browser fixtures are always registered.
"""

import pytest
from playwright.sync_api import sync_playwright

from utils.config import Config
from utils.logger import get_logger
from utils.screenshot_utils import capture_failure_screenshot
from utils.video_utils import get_video_context_options

logger = get_logger(__name__)

Config.ensure_report_dirs()


def _resolve_headless(request) -> bool:
    """Determine headless mode from CLI flags or .env fallback."""
    if request.config.getoption("--headed", default=False):
        return False
    if request.config.getoption("--headless", default=False):
        return True
    return Config.HEADLESS


@pytest.fixture(scope="session")
def browser_type_launch_args(request):
    """Return browser launch arguments from CLI flags or environment config."""
    headless = _resolve_headless(request)
    Config.log_startup_summary(headless=headless)

    return {
        "headless": headless,
        "slow_mo": Config.SLOW_MO,
    }


@pytest.fixture(scope="session")
def browser_context_args():
    """Return browser context arguments including video recording options."""
    video_opts = get_video_context_options()
    base_args = {
        "viewport": {"width": 1920, "height": 1080},
        "ignore_https_errors": True,
    }
    if video_opts:
        base_args.update(video_opts)
    return base_args


@pytest.fixture(scope="session")
def playwright_instance():
    """Start a Playwright session for the entire test run."""
    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture(scope="session")
def browser(playwright_instance, browser_type_launch_args):
    """Launch a Chromium browser for the test session."""
    browser = playwright_instance.chromium.launch(**browser_type_launch_args)
    yield browser
    browser.close()


@pytest.fixture
def context(browser, browser_context_args, request):
    """Create a fresh browser context per test with optional tracing."""
    context = browser.new_context(**browser_context_args)

    if Config.TRACE:
        context.tracing.start(screenshots=True, snapshots=True, sources=True)

    yield context

    if Config.TRACE:
        trace_path = Config.TRACES_DIR / f"{request.node.name}.zip"
        context.tracing.stop(path=str(trace_path))
        logger.info("Trace saved: %s", trace_path)

    context.close()


@pytest.fixture
def page(context):
    """Provide a fresh Page per test from the browser context."""
    page = context.new_page()
    page.set_default_timeout(Config.DEFAULT_TIMEOUT)
    page.set_default_navigation_timeout(Config.NAVIGATION_TIMEOUT)
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
