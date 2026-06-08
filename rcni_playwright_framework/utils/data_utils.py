"""
JSON test-data loaders for issuers and RCNI filter configuration.

Keeps issuer lists and search filters out of test code so new
issuers or date ranges can be added without modifying Python files.
"""

import json
from pathlib import Path
from typing import Any

from utils.config import Config
from utils.logger import get_logger

logger = get_logger(__name__)


def load_json(filename: str) -> dict:
    """
    Load and parse a JSON file from the test_data directory.

    Use as the base loader for issuers.json and rcni_filters.json.

    Args:
        filename: JSON filename relative to test_data/.

    Returns:
        Parsed JSON as a dictionary.

    Raises:
        FileNotFoundError: If the file does not exist.
        json.JSONDecodeError: If the file is not valid JSON.
    """
    filepath = Config.TEST_DATA_DIR / filename
    logger.info("Loading test data: %s", filepath)

    with open(filepath, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_issuers(run_mode: str = "all") -> list[str]:
    """
    Load issuer IDs from test_data/issuers.json.

    Supports run_mode filtering: 'all', 'smoke' (first issuer only),
    or a custom list defined in the JSON under 'smoke_issuers'.

    Args:
        run_mode: Execution mode from rcni_filters.json or CLI override.

    Returns:
        List of issuer ID strings to iterate in tests.
    """
    data = load_json("issuers.json")
    all_issuers: list[str] = data.get("issuers", [])

    if run_mode == "smoke":
        smoke_subset = data.get("smoke_issuers", all_issuers[:1])
        logger.info("Smoke mode: running %d issuer(s)", len(smoke_subset))
        return smoke_subset

    logger.info("Running all %d issuers", len(all_issuers))
    return all_issuers


def load_rcni_filters() -> dict[str, Any]:
    """
    Load month, year, issuer list override, and run_mode from rcni_filters.json.

    Use at the start of RCNI report tests to drive dropdown selections
    without hard-coding values in page objects or test functions.

    Returns:
        Dict with keys: month, month_label, year, run_mode, issuers (optional).
    """
    filters = load_json("rcni_filters.json")
    logger.info(
        "RCNI filters loaded: month=%s year=%s run_mode=%s",
        filters.get("month"),
        filters.get("year"),
        filters.get("run_mode"),
    )
    return filters
