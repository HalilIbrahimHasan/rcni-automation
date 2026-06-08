"""
Locator definitions for the RCNI Reconciliation Workbench.

Preserves data-testid locators from the legacy framework and adds
role-based and text-based fallbacks for resilient navigation.
"""


class RCNILocators:
    """Centralised RCNI page locator constants and resolver hints."""

    # ----- Navigation -----
    ENROLLMENT_TEST_ID = "Enrollment"
    RECONCILIATION_LINK_ROLE = "link"
    RECONCILIATION_LINK_NAME = "Reconciliation Workbench End"
    RECONCILIATION_LINK_TEXT = "Reconciliation Workbench End"

    # ----- Filters (primary: data-testid) -----
    ISSUER_DROPDOWN_TEST_ID = "issuerName"
    MONTH_DROPDOWN_TEST_ID = "reconciliationMonth"
    YEAR_DROPDOWN_TEST_ID = "reconciliationYear"
    GO_BUTTON_TEST_ID = "reconciliationGoButton"

    # ----- Filter fallbacks -----
    ISSUER_DROPDOWN_CSS = "[data-testid='issuerName'], select[name='issuerName']"
    MONTH_DROPDOWN_CSS = "[data-testid='reconciliationMonth']"
    YEAR_DROPDOWN_CSS = "[data-testid='reconciliationYear']"
    GO_BUTTON_CSS = "[data-testid='reconciliationGoButton'], button:has-text('Go')"

    # ----- Table headings -----
    HEADING_FILE_NAME = "table-heading-0"
    HEADING_REPORT_NAME = "table-heading-9"
    HEADING_STATUS = "table-heading-2"

    # ----- Report content indicators -----
    TOP_DISCREPANCIES_TEXT = "TOP 5 DISCREPANCIES"
    ISSUER_ACTIVITY_TEXT = "Issuer Activity"

    # ----- Chart sections (CSS fallback — no stable testid available) -----
    CHART_MAIN_CSS = ".css-15rufqy"
    CHART_SECONDARY_CSS = ".css-h1sary"

    # ----- Status label pattern -----
    # Format with issuer name and month, e.g. "{issuer} - MAY - Status"
    STATUS_LABEL_TEMPLATE = "{} - {} - Status"
