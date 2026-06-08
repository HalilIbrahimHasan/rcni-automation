"""
HTML report generation and RCNI table row extraction utilities.

Builds issuer-team HTML reports from captured rows and screenshots,
and extracts structured data from the RCNI reconciliation table.
"""

from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

from playwright.sync_api import Page

from utils.config import Config
from utils.logger import get_logger

logger = get_logger(__name__)


def extract_report_rows(page: Page) -> list[dict[str, str]]:
    """
    Extract report rows from the RCNI reconciliation results table.

    Reads table cells by data-testid pattern and returns a list of
    row dictionaries. Use after clicking Go and waiting for results.

    Args:
        page: Active Playwright Page on the RCNI report view.

    Returns:
        List of dicts with file_name, status, report_name, etc.
    """
    rows = []
    row_index = 0

    while True:
        report_cell = page.get_by_test_id(f"table-row-{row_index}-cell-9")
        try:
            report_cell.wait_for(state="visible", timeout=3000)
        except Exception:
            break

        def cell_text(col: int) -> str:
            try:
                locator = page.get_by_test_id(f"table-row-{row_index}-cell-{col}")
                return locator.inner_text().strip()
            except Exception:
                return ""

        row_data = {
            "file_name": cell_text(0),
            "received_date": cell_text(1),
            "status": cell_text(2),
            "in_file": cell_text(3),
            "in_hix": cell_text(4),
            "success": cell_text(5),
            "discrepancies": cell_text(6),
            "errors": cell_text(7),
            "total_discrepancies": cell_text(8),
            "report_name": cell_text(9),
            "report_date": cell_text(10) if page.get_by_test_id(
                f"table-row-{row_index}-cell-10"
            ).count() > 0 else "",
        }
        rows.append(row_data)
        row_index += 1

    logger.info("Extracted %d report row(s)", len(rows))
    return rows


def build_issuer_html_report(
    issuer_results: list[dict[str, Any]],
    output_filename: str = "issuer_report.html",
    month: str = "",
    year: str = "",
) -> str:
    """
    Generate an HTML report summarising all issuer capture results.

    Includes issuer name, month/year, status, report rows, screenshot
    links, and failure reasons. Use at the end of issuer loop tests.

    Args:
        issuer_results: List of per-issuer result dicts from tests.
        output_filename: HTML filename inside reports/html/.
        month: Selected reconciliation month label.
        year: Selected reconciliation year.

    Returns:
        Absolute path string to the generated HTML file.
    """
    Config.ensure_report_dirs()
    output_path = Config.HTML_DIR / output_filename
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html_parts = [
        "<!DOCTYPE html>",
        "<html lang='en'>",
        "<head>",
        "<meta charset='UTF-8'>",
        "<title>RCNI Issuer Report</title>",
        "<style>",
        "body { font-family: Arial, sans-serif; margin: 24px; }",
        "table { border-collapse: collapse; width: 100%; margin-bottom: 24px; }",
        "th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }",
        "th { background: #2c3e50; color: #fff; }",
        ".failed { background: #fdecea; }",
        ".no-report { background: #fff8e1; }",
        ".screenshot-link { display: block; margin: 4px 0; }",
        "h2 { color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 4px; }",
        "</style>",
        "</head>",
        "<body>",
        f"<h1>RCNI Issuer Report</h1>",
        f"<p>Generated: {escape(generated_at)} | Month: {escape(month)} | Year: {escape(year)}</p>",
    ]

    for result in issuer_results:
        issuer = escape(str(result.get("issuer", "")))
        issuer_name = escape(str(result.get("issuer_name", issuer)))
        status = "FAILED" if result.get("failure_reason") else (
            "NO REPORT" if result.get("no_report") else "OK"
        )
        row_class = "failed" if status == "FAILED" else ("no-report" if status == "NO REPORT" else "")

        html_parts.append(f"<h2>Issuer: {issuer_name} ({issuer}) — {status}</h2>")

        if result.get("failure_reason"):
            html_parts.append(
                f"<p><strong>Failure:</strong> {escape(str(result['failure_reason']))}</p>"
            )

        screenshots = result.get("screenshots", {})
        if screenshots:
            html_parts.append("<h3>Screenshots</h3>")
            for label, path in screenshots.items():
                html_parts.append(
                    f"<a class='screenshot-link' href='file://{escape(str(path))}'>"
                    f"{escape(label)}</a>"
                )

        report_rows = result.get("report_rows", [])
        if report_rows:
            html_parts.append("<table>")
            html_parts.append("<tr>")
            for key in report_rows[0]:
                html_parts.append(f"<th>{escape(key.replace('_', ' ').title())}</th>")
            html_parts.append("</tr>")

            for row in report_rows:
                html_parts.append(f"<tr class='{row_class}'>")
                for value in row.values():
                    html_parts.append(f"<td>{escape(str(value))}</td>")
                html_parts.append("</tr>")
            html_parts.append("</table>")
        else:
            html_parts.append("<p>No report rows captured.</p>")

    html_parts.extend(["</body>", "</html>"])

    output_path.write_text("\n".join(html_parts), encoding="utf-8")
    logger.info("HTML report written: %s", output_path)
    return str(output_path)
