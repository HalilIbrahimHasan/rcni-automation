"""
Framework-level conftest — ensures imports work when running from
inside rcni_playwright_framework/ and loads shared Playwright fixtures.
"""

import sys
from pathlib import Path

# Ensure framework root is on sys.path for pages/utils/locators imports
_FRAMEWORK_ROOT = Path(__file__).resolve().parent
if str(_FRAMEWORK_ROOT) not in sys.path:
    sys.path.insert(0, str(_FRAMEWORK_ROOT))

# Register all Playwright fixtures (page, browser, context, etc.)
pytest_plugins = ["playwright_fixtures"]
