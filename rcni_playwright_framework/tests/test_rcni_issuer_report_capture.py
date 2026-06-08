"""
Regression tests for RCNI issuer report capture and HTML reporting.

Iterates issuers from JSON, applies filters, captures screenshots
and table rows, and generates an HTML summary report.
"""

import pytest

from pages.login_page import LoginPage
from pages.rcni_dashboard_page import RCNIDashboardPage
from pages.rcni_report_page import RCNIReportPage
from utils.data_utils import load_issuers, load_rcni_filters
from utils.logger import get_logger
from utils.report_utils import build_issuer_html_report

logger = get_logger(__name__)


@pytest.mark.regression
@pytest.mark.rcni
def test_rcni_issuer_report_capture(page):
    """
    Log in, navigate to RCNI, and capture reports for all JSON issuers.

    For each issuer: apply month/year filters, extract table rows,
    capture screenshots, and build a combined HTML report.
    """
    filters = load_rcni_filters()
    run_mode = filters.get("run_mode", "all")

    custom_issuers = filters.get("issuers", [])
    issuers = custom_issuers if custom_issuers else load_issuers(run_mode=run_mode)

    month = filters.get("month", "5")
    month_label = filters.get("month_label", "May")
    year = filters.get("year", "2025")

    login_page = LoginPage(page)
    login_page.goto()
    login_page.login()

    dashboard = RCNIDashboardPage(page)
    dashboard.navigate_to_reconciliation()

    report_page = RCNIReportPage(page)
    issuer_results = []

    for issuer_id in issuers:
        logger.info("Processing issuer: %s", issuer_id)

        issuer_result = {
            "issuer": issuer_id,
            "issuer_name": issuer_id,
            "screenshots": {},
            "report_rows": [],
            "no_report": False,
            "failure_reason": None,
        }

        try:
            issuer_name = dashboard.apply_filters(
                issuer_id=issuer_id,
                month=month,
                year=year,
                month_label=month_label,
            )
            issuer_result["issuer_name"] = issuer_name

            report_page.wait_for_report_content()
            issuer_result["report_rows"] = report_page.get_report_rows()

            if not issuer_result["report_rows"]:
                issuer_result["no_report"] = True
                logger.warning("No report rows for issuer %s", issuer_id)
            else:
                logger.info(
                    "Captured %d row(s) for issuer %s",
                    len(issuer_result["report_rows"]),
                    issuer_id,
                )

            issuer_result["screenshots"] = report_page.capture_issuer_report(issuer_id)
            issuer_results.append(issuer_result)

        except Exception as exc:
            artifacts = dashboard.capture_failure_artifacts(issuer_id, suffix="issuer")
            issuer_result["screenshots"] = {"Failure Screenshot": artifacts["screenshot"]}
            issuer_result["failure_reason"] = str(exc)
            issuer_result["report_rows"].append({
                "file_name": "",
                "received_date": "",
                "status": "FAILED",
                "in_file": "",
                "in_hix": "",
                "success": "",
                "discrepancies": "",
                "errors": "",
                "total_discrepancies": "",
                "report_name": str(exc),
                "report_date": "",
            })
            issuer_results.append(issuer_result)
            logger.error("Issuer %s failed: %s", issuer_id, exc)
            raise

        finally:
            dashboard.return_to_dashboard()

    report_path = build_issuer_html_report(
        issuer_results,
        output_filename="issuer_report.html",
        month=month_label,
        year=year,
    )
    logger.info("HTML report created: %s", report_path)


@pytest.mark.smoke
@pytest.mark.rcni
def test_rcni_single_issuer_smoke(page):
    """
    Smoke test: capture report for the first smoke issuer only.

    Uses run_mode='smoke' from issuers.json smoke_issuers list.
    """
    filters = load_rcni_filters()
    filters["run_mode"] = "smoke"
    issuers = load_issuers(run_mode="smoke")

    login_page = LoginPage(page)
    login_page.goto()
    login_page.login()

    dashboard = RCNIDashboardPage(page)
    dashboard.navigate_to_reconciliation()

    report_page = RCNIReportPage(page)
    issuer_id = issuers[0]

    issuer_name = dashboard.apply_filters(
        issuer_id=issuer_id,
        month=filters.get("month", "5"),
        year=filters.get("year", "2025"),
        month_label=filters.get("month_label", "May"),
    )

    report_page.wait_for_report_content()
    rows = report_page.get_report_rows()
    screenshots = report_page.capture_issuer_report(issuer_id)

    logger.info(
        "Smoke capture complete: issuer=%s name=%s rows=%d screenshots=%d",
        issuer_id,
        issuer_name,
        len(rows),
        len(screenshots),
    )
