# RCNI Playwright Automation Framework

A scalable Playwright + Pytest UI automation framework for the RCNI / Georgia Access reconciliation workflow. Built with the Page Object Model, JSON-driven test data, dynamic waits, and comprehensive artifact capture (screenshots, videos, traces, HTML reports).

## Project Purpose

This framework automates:

- **GA Login** — Authenticate via environment-configured credentials
- **RCNI Navigation** — Enrollment → Reconciliation Workbench End
- **Issuer Report Capture** — Loop through JSON-defined issuers, apply month/year filters, extract table rows, and capture screenshots
- **834 Download** — Navigate the GetInsured folder tree by name and download 834 files

## Project Structure

```
rcni_playwright_framework/
├── pages/              # Page Object Model classes
├── locators/           # Centralised locator definitions
├── tests/              # Pytest test modules
├── utils/              # Config, waits, screenshots, reports, data loaders
├── test_data/          # JSON issuer list and RCNI filters
├── reports/            # Screenshots, videos, traces, HTML, downloads
├── conftest.py         # Browser fixtures and failure hooks
├── pytest.ini          # Markers and discovery config
└── requirements.txt    # Python dependencies
```

## Setup

### 1. Create a Virtual Environment

```bash
cd rcni_playwright_framework
python3 -m venv .venv
source .venv/bin/activate        # macOS / Linux
# .venv\Scripts\activate         # Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
playwright install chromium
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your values:

| Variable | Description |
|----------|-------------|
| `GA_URL` | Georgia Access portal URL |
| `GA_EMAIL` | Login email |
| `GA_PASSWORD` | Login password |
| `HEADLESS` | `true` / `false` |
| `SLOW_MO` | Delay between actions (ms) |
| `VIDEO` | Enable video recording |
| `TRACE` | Enable Playwright tracing |

## Running Tests

### All tests

```bash
pytest
```

### By marker

```bash
pytest -m smoke
pytest -m regression
pytest -m rcni
pytest -m download
```

### Specific test file (headed mode)

```bash
pytest tests/test_rcni_login_and_navigation.py --headed
```

### With HTML report

```bash
pytest -m rcni --html=reports/html/report.html
```

### Smoke issuer capture only

```bash
pytest tests/test_rcni_issuer_report_capture.py::test_rcni_single_issuer_smoke -m smoke
```

## Artifact Locations

| Artifact | Path |
|----------|------|
| Screenshots | `reports/screenshots/` |
| Failure screenshots | `reports/failures/` |
| Videos | `reports/videos/` |
| Traces | `reports/traces/` |
| HTML reports | `reports/html/` |
| Downloads | `reports/downloads/` |

## Adding New Issuers

Edit `test_data/issuers.json`:

```json
{
  "issuers": ["82824", "83761", "NEW_ISSUER_ID"],
  "smoke_issuers": ["82824"]
}
```

No Python code changes are required — tests load issuers from JSON at runtime.

## Updating Filters (Month / Year / Run Mode)

Edit `test_data/rcni_filters.json`:

```json
{
  "month": "5",
  "month_label": "May",
  "year": "2025",
  "run_mode": "all",
  "issuers": []
}
```

Set `run_mode` to `"smoke"` to run only `smoke_issuers`. Override the issuer list by populating the `issuers` array.

## Updating Locators

Locators live in `locators/` and follow this priority:

1. `data-testid` (preferred)
2. Role-based (`get_by_role`)
3. Text-based (`get_by_text`)
4. CSS fallback (last resort)

Example — add a new RCNI locator in `locators/rcni_locators.py`:

```python
NEW_ELEMENT_TEST_ID = "myNewElement"
```

Then reference it in the page object via `self.resolve_by_test_id(L.NEW_ELEMENT_TEST_ID)`.

## Extending the Framework

- **New pages** — Create a class in `pages/` inheriting from `BasePage`
- **New locators** — Add constants to the appropriate file in `locators/`
- **New tests** — Add a file in `tests/` with the appropriate `@pytest.mark` decorators
- **New utilities** — Add helpers to `utils/` and import in page objects or tests

## Key Design Decisions

- **No hard-coded waits** — Uses `safe_click`, `safe_fill`, `wait_for_visible` instead of `wait_for_timeout`
- **Retry-friendly helpers** — Base page methods retry transient failures
- **JSON-driven data** — Issuers and filters are externalised from test code
- **Failure artifacts** — Screenshots, videos, and traces captured automatically on failure
