"""
Workspace-root conftest — sets up sys.path when pytest runs from
the parent 'rcni automation' folder. Fixtures live in the framework conftest.
"""

import sys
from pathlib import Path

_FRAMEWORK_ROOT = Path(__file__).resolve().parent / "rcni_playwright_framework"
if str(_FRAMEWORK_ROOT) not in sys.path:
    sys.path.insert(0, str(_FRAMEWORK_ROOT))
