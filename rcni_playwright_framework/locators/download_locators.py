"""
Locator definitions for the GetInsured 834 file download page.

Uses folder-name and role-based strategies instead of fragile
nth-child row selectors wherever possible.
"""


class DownloadLocators:
    """Centralised 834 download page locator constants."""

    # Login (GetInsured portal — different from GA login)
    USERNAME_ROLE = "textbox"
    USERNAME_NAME = "Username Or Email"

    PASSWORD_ROLE = "textbox"
    PASSWORD_NAME = "Password"

    SIGN_IN_BUTTON_ROLE = "button"
    SIGN_IN_BUTTON_NAME = "sign-in-btn"

    # Folder tree navigation
    FOLDER_ROW_CSS = "tr:has(.name-td)"
    FOLDER_NAME_CELL_CSS = ".name-td"
    FOLDER_CHEVRON_CSS = ".icon-chevron-right"
    FOLDER_CHECKBOX_CSS = ".table-td.check-td"

    # Download action
    DOWNLOAD_LINK_ROLE = "link"
    DOWNLOAD_LINK_NAME = "Download"

    # Default folder path segments for 834 archive navigation
    DEFAULT_FOLDER_PATH = ["archive", "in", "good", "834"]
