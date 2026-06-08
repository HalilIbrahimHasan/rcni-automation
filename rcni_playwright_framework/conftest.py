"""
Pytest fixtures and hooks for the RCNI Playwright framework.

Provides browser, context, and page fixtures with video/trace
recording, plus automatic failure screenshot capture.
"""

import pytest
from playwright.sync_api import sync_playwright

from utils.config import Config
from utils.logger import get_logger
from utils.screenshot_utils import capture_failure_screenshot
from utils.video_utils import get_video_context_options

logger = get_logger(__name__)

Config.ensure_report_dirs()


def pytest_addoption(parser):
    """
    Register CLI flags for browser display mode.

    --headed and --headless override the HEADLESS value from .env.
    """
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


def _resolve_headless(request) -> bool:
    """
    Determine headless mode from CLI flags or .env fallback.

    Priority: --headed > --headless > HEADLESS env var.
    """
    if request.config.getoption("--headed"):
        return False
    if request.config.getoption("--headless"):
        return True
    return Config.HEADLESS


@pytest.fixture(scope="session")
def browser_type_launch_args(request):
    """
    Return browser launch arguments from CLI flags or environment config.

    Controls headless mode and slow_mo delay for debugging.
    """
    headless = _resolve_headless(request)
    mode = "headless" if headless else "headed"
    logger.info("Browser launch mode: %s", mode)

    return {
        "headless": headless,
        "slow_mo": Config.SLOW_MO,
    }


@pytest.fixture(scope="session")
def browser_context_args():
    """
    Return browser context arguments including video recording options.

    Videos are saved to reports/videos/ when Config.VIDEO is enabled.
    """
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
    """
    Start a Playwright session for the entire test run.

    Yields the sync_playwright manager; stops on teardown.
    """
    with sync_playwright() as playwright:
        yield playwright


@pytest.fixture(scope="session")
def browser(playwright_instance, browser_type_launch_args):
    """
    Launch a Chromium browser for the test session.

    Args:
        playwright_instance: Session-scoped Playwright manager.
        browser_type_launch_args: Headless and slow_mo settings.
    """
    browser = playwright_instance.chromium.launch(**browser_type_launch_args)
    yield browser
    browser.close()


@pytest.fixture
def context(browser, browser_context_args, request):
    """
    Create a fresh browser context per test with optional tracing.

    Starts Playwright tracing when Config.TRACE is enabled and
    saves the trace zip to reports/traces/ on teardown.
    """
    context = browser.new_context(**browser_context_args)

    if Config.TRACE:
        context.tracing.start(screenshots=True, snapshots=True, sources=True)

    yield context

    trace_path = None
    if Config.TRACE:
        trace_path = Config.TRACES_DIR / f"{request.node.name}.zip"
        context.tracing.stop(path=str(trace_path))
        logger.info("Trace saved: %s", trace_path)

    context.close()


@pytest.fixture
def page(context):
    """
    Provide a fresh Page per test from the browser context.

    Use in all test functions as the primary browser interaction surface.
    """
    page = context.new_page()
    page.set_default_timeout(Config.DEFAULT_TIMEOUT)
    page.set_default_navigation_timeout(Config.NAVIGATION_TIMEOUT)
    yield page
    page.close()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Store test phase results on the item for failure screenshot hooks.

    Attaches rep_setup, rep_call, and rep_teardown attributes
    so autouse fixtures can inspect pass/fail state.
    """
    outcome = yield
    rep = outcome.get_result()
    setattr(item, "rep_" + rep.when, rep)


@pytest.fixture(autouse=True)
def screenshot_on_failure(request, page):
    """
    Capture a full-page failure screenshot when a test call phase fails.

    Saves to reports/failures/{test_name}.png automatically.
    """
    yield

    rep = getattr(request.node, "rep_call", None)
    if rep and rep.failed:
        shot = capture_failure_screenshot(page, request.node.name)
        logger.error("Test failure screenshot: %s", shot)
