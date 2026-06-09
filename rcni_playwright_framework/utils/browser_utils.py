"""
Browser launch utilities for Playwright.

Handles Chrome/Chromium/Edge/Firefox/WebKit launch with robust
arguments for headed mode on Windows, plus automatic fallbacks
when the primary browser fails to open.
"""

from typing import Any, Optional

from playwright.sync_api import Browser, Playwright

from utils.config import Config
from utils.logger import get_logger

logger = get_logger(__name__)

# Supported BROWSER values in .env
SUPPORTED_BROWSERS = ("chromium", "chrome", "msedge", "firefox", "webkit")

# Chrome/Chromium args that help the window actually appear on screen (Windows/macOS)
HEADED_BROWSER_ARGS = [
    "--start-maximized",
    "--window-position=0,0",
    "--disable-infobars",
    "--disable-extensions",
    "--no-first-run",
    "--no-default-browser-check",
    "--disable-popup-blocking",
    "--disable-translate",
    "--ignore-certificate-errors",
    "--disable-blink-features=AutomationControlled",
]

# Extra stability args (VMs, corporate laptops, GPU issues)
STABILITY_BROWSER_ARGS = [
    "--disable-gpu-sandbox",
    "--disable-software-rasterizer",
    "--disable-dev-shm-usage",
    "--no-sandbox",
]

HEADLESS_BROWSER_ARGS = [
    "--disable-gpu",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--window-size=1920,1080",
]


def _parse_extra_args(raw: str) -> list[str]:
    """Parse comma-separated extra browser args from .env."""
    if not raw or not raw.strip():
        return []
    return [arg.strip() for arg in raw.split(",") if arg.strip()]


def build_browser_args(headless: bool) -> list[str]:
    """
    Build the full list of Chromium/Chrome launch arguments.

    Headed mode uses maximize + window position args so the browser
    is visible on screen. Headless uses GPU-off args for stability.
    """
    if headless:
        args = list(HEADLESS_BROWSER_ARGS)
    else:
        args = list(HEADED_BROWSER_ARGS)
        if Config.BROWSER_STABILITY_ARGS:
            args.extend(STABILITY_BROWSER_ARGS)

    args.extend(_parse_extra_args(Config.BROWSER_EXTRA_ARGS))

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for arg in args:
        if arg not in seen:
            seen.add(arg)
            unique.append(arg)
    return unique


def _base_launch_options(headless: bool) -> dict[str, Any]:
    """Common launch options shared across Chromium-based browsers."""
    options: dict[str, Any] = {
        "headless": headless,
        "slow_mo": Config.SLOW_MO,
        "args": build_browser_args(headless),
    }
    if Config.BROWSER_EXECUTABLE:
        options["executable_path"] = Config.BROWSER_EXECUTABLE
    return options


def _channel_for_browser(browser_name: str) -> Optional[str]:
    """
    Map browser name to Playwright channel.

    'chrome' and 'msedge' use installed system browsers via channel.
    """
    if Config.BROWSER_CHANNEL:
        return Config.BROWSER_CHANNEL

    mapping = {
        "chrome": "chrome",
        "msedge": "msedge",
    }
    return mapping.get(browser_name)


def _get_launcher(playwright: Playwright, browser_name: str):
    """Return the Playwright browser type object (chromium, firefox, webkit)."""
    if browser_name in ("chromium", "chrome", "msedge"):
        return playwright.chromium
    if browser_name == "firefox":
        return playwright.firefox
    if browser_name == "webkit":
        return playwright.webkit
    raise ValueError(
        f"Unsupported BROWSER='{browser_name}'. "
        f"Use one of: {', '.join(SUPPORTED_BROWSERS)}"
    )


def _attempt_launch(
    playwright: Playwright,
    browser_name: str,
    headless: bool,
    label: str,
) -> Browser:
    """
    Try launching a single browser configuration.

    Raises on failure so the caller can try the next fallback.
    """
    launcher = _get_launcher(playwright, browser_name)
    options = _base_launch_options(headless)

    channel = _channel_for_browser(browser_name)
    if channel and browser_name in ("chromium", "chrome", "msedge"):
        options["channel"] = channel

    logger.info(
        "Launching browser [%s]: type=%s channel=%s headless=%s args=%d",
        label,
        browser_name,
        channel or "bundled",
        headless,
        len(options.get("args", [])),
    )

    browser = launcher.launch(**options)
    logger.info("Browser launched successfully [%s]", label)
    return browser


def build_context_options(headless: bool) -> dict[str, Any]:
    """
    Build browser context options.

    Uses no_viewport in headed mode so --start-maximized works correctly.
    """
    from utils.video_utils import get_video_context_options

    if headless:
        context_opts: dict[str, Any] = {
            "viewport": {"width": 1920, "height": 1080},
            "ignore_https_errors": True,
        }
    else:
        context_opts = {
            "no_viewport": True,
            "ignore_https_errors": True,
        }

    video_opts = get_video_context_options()
    if video_opts:
        context_opts.update(video_opts)

    return context_opts


def launch_browser(
    playwright: Playwright,
    headless: bool,
    browser_name: Optional[str] = None,
) -> Browser:
    """
    Launch browser with automatic fallbacks.

    Tries, in order:
      1. Configured BROWSER from .env (or browser_name override)
      2. Installed Google Chrome (channel=chrome)
      3. Installed Microsoft Edge (channel=msedge)
      4. Playwright bundled Chromium (no channel)

    Use when headed Chrome fails silently on Windows/corporate machines.
    """
    primary = (browser_name or Config.BROWSER).lower().strip()
    fallbacks: list[tuple[str, str]] = [(primary, "primary (.env)")]

    if primary != "chrome":
        fallbacks.append(("chrome", "fallback: installed Chrome"))
    if primary != "msedge":
        fallbacks.append(("msedge", "fallback: installed Edge"))
    if primary != "chromium":
        fallbacks.append(("chromium", "fallback: bundled Chromium"))

    # Deduplicate browser names while keeping first label
    seen: set[str] = set()
    attempts: list[tuple[str, str]] = []
    for name, label in fallbacks:
        if name not in seen and name in SUPPORTED_BROWSERS:
            seen.add(name)
            attempts.append((name, label))

    last_error: Optional[Exception] = None

    for browser_name, label in attempts:
        try:
            return _attempt_launch(playwright, browser_name, headless, label)
        except Exception as exc:
            last_error = exc
            logger.warning("Browser launch failed [%s]: %s", label, exc)

    raise RuntimeError(
        f"All browser launch attempts failed. Last error: {last_error}"
    ) from last_error


def log_browser_config(headless: bool) -> None:
    """Log browser-related configuration at startup."""
    logger.info("Browser type  : %s", Config.BROWSER)
    logger.info("Browser channel: %s", Config.BROWSER_CHANNEL or "(auto)")
    logger.info(
        "Browser mode  : %s",
        "headless (invisible)" if headless else "headed (visible)",
    )
    if Config.BROWSER_EXECUTABLE:
        logger.info("Executable    : %s", Config.BROWSER_EXECUTABLE)
    logger.info("Chrome args   : %d configured", len(build_browser_args(headless)))
