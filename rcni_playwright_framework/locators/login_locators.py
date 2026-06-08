"""
Locator definitions for the Georgia Access login page.

Defines primary and fallback locator strategies following the
priority order: data-testid → role → text → CSS.
"""


class LoginLocators:
    """Centralised login page locator constants and resolver hints."""

    # Primary: role-based locators (preferred for accessible forms)
    EMAIL_ROLE = "textbox"
    EMAIL_NAME = "Email Address"

    PASSWORD_ROLE = "textbox"
    PASSWORD_NAME = "Password"

    LOGIN_BUTTON_ROLE = "button"
    LOGIN_BUTTON_NAME = "Login"

    # Post-login success indicator
    ENROLLMENT_TEST_ID = "Enrollment"

    # Fallback CSS selectors (used only when role/testid fail)
    EMAIL_CSS = "input[type='email'], input[name='email'], #email"
    PASSWORD_CSS = "input[type='password'], input[name='password'], #password"
    LOGIN_BUTTON_CSS = "button[type='submit'], .login-button, #login-btn"
