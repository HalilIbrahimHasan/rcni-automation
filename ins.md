Create a brand-new Playwright Python + Pytest UI automation framework for the RCNI / Georgia Access workflow.

IMPORTANT:
- Do NOT run, open, test, or validate the real URL.
- Do NOT use real credentials.
- Create a `.env.example` file with dummy values only:
  GA_URL=https://dummy-url.example.com
  GA_EMAIL=dummy@example.com
  GA_PASSWORD=dummy_password
  HEADLESS=false
  SLOW_MO=200
  VIDEO=true
  TRACE=true

Use the uploaded existing files only as reference. Current code already has:
- Login flow using GA_URL / GA_EMAIL / GA_PASSWORD from environment variables.
- RCNI navigation through Enrollment → Reconciliation Workbench End.
- Issuer/month/year dropdown selection.
- Screenshot capture, report row extraction, and HTML report generation.
- Static issuer list.
- Some fragile locators and hard-coded waits that need to be redesigned.

Build a clean, scalable framework with this structure:

rcni_playwright_framework/
│
├── pages/
│   ├── base_page.py
│   ├── login_page.py
│   ├── rcni_dashboard_page.py
│   ├── rcni_report_page.py
│   └── getinsured_834_download_page.py
│
├── locators/
│   ├── login_locators.py
│   ├── rcni_locators.py
│   └── download_locators.py
│
├── tests/
│   ├── test_rcni_login_and_navigation.py
│   ├── test_rcni_issuer_report_capture.py
│   └── test_834_download_flow.py
│
├── utils/
│   ├── config.py
│   ├── logger.py
│   ├── wait_utils.py
│   ├── screenshot_utils.py
│   ├── video_utils.py
│   ├── report_utils.py
│   ├── file_utils.py
│   └── data_utils.py
│
├── test_data/
│   ├── issuers.json
│   └── rcni_filters.json
│
├── reports/
│   ├── screenshots/
│   ├── videos/
│   ├── traces/
│   ├── html/
│   └── failures/
│
├── conftest.py
├── pytest.ini
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md

Framework requirements:

1. Use Playwright sync API with pytest.
2. Use Page Object Model.
3. Use environment variables via python-dotenv.
4. Add strong dynamic wait handling.
5. Avoid hard-coded wait_for_timeout unless absolutely necessary.
6. Add retry-friendly helper methods:
   - safe_click()
   - safe_fill()
   - safe_select_dropdown()
   - wait_for_visible()
   - wait_for_url_or_element()
   - capture_failure_artifacts()
7. Locator strategy must be dynamic and resilient:
   - Prefer data-testid.
   - Then role-based locator.
   - Then text-based locator.
   - Then CSS fallback.
   - Avoid nth-child unless no other option exists.
8. Add screenshot capture:
   - Login page
   - After login
   - RCNI landing page
   - After issuer/month/year search
   - Full page screenshots per issuer
   - Failure screenshots
9. Add video recording support through Playwright browser context.
10. Add trace recording support.
11. Add HTML report generation:
   - issuer name
   - selected month/year
   - status
   - captured report rows
   - screenshot links
   - failure reason if any
12. Add JSON-driven issuer execution:
   - test_data/issuers.json should hold issuer IDs.
   - Do not hard-code issuer list inside test.
13. Add JSON-driven filters:
   - month
   - year
   - issuer list
   - run mode
14. Add 834 download page support:
   - navigate folder tree dynamically
   - avoid nth-child selectors where possible
   - capture screenshot before download
   - expect_download with configurable timeout
   - save downloaded file into reports/downloads/
15. Add pytest markers:
   - smoke
   - regression
   - rcni
   - download
16. Add CLI usage examples:
   pytest -m smoke
   pytest tests/test_rcni_login_and_navigation.py --headed
   pytest -m rcni --html=reports/html/report.html
17. Add README explaining:
   - project purpose
   - setup
   - virtual environment creation
   - install dependencies
   - playwright install
   - .env setup
   - how to run tests
   - where screenshots/videos/traces/reports are saved
   - how to add new issuers
   - how to update locators
18. Add code comments/docstrings for every method explaining:
   - what it does
   - why it exists
   - when it should be used
19. Do not execute real login or real URL.
20. Make the framework production-ready but safe for local development.

Important improvements over current files:
- Existing login_page.py uses GA_URL and waits for Email Address, Password, Login, and Enrollment. Keep the idea but move it into a cleaner LoginPage class with better error handling.
- Existing rcni_locators.py has useful data-testid locators for Enrollment, issuerName, reconciliationMonth, reconciliationYear, and reconciliationGoButton. Keep them but add fallback locators.
- Existing test_rcni_login.py has a working high-level issuer loop idea, but move issuer data to JSON and make the test smaller by using page objects and utilities.
- Existing getinsured_834_download_page.py has a folder download flow, but replace fragile nth-child folder navigation with more dynamic folder-name based methods where possible.

Generate all files with complete code.
Do not leave placeholders except dummy .env values.
Make sure imports are correct.
Make sure pytest can discover the tests.
Make sure the framework can be extended later for more issuers, months, years, screenshots, videos, and downloads.