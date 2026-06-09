# RCNI Framework — one-time setup (Windows PowerShell)
# REQUIRES Python 3.11 or 3.12 (NOT 3.14 — Playwright will timeout)
# Run:  cd rcni_playwright_framework
#       .\setup.ps1

Write-Host "=== RCNI Framework Setup ===" -ForegroundColor Cyan

# Prefer Python 3.12, then 3.11
$pythonCmd = $null
foreach ($ver in @("3.12", "3.11")) {
    try {
        $null = & py "-$ver" -c "import sys; print(sys.version)" 2>$null
        if ($LASTEXITCODE -eq 0) {
            $pythonCmd = "py -$ver"
            Write-Host "Using Python $ver" -ForegroundColor Green
            break
        }
    } catch {}
}

if (-not $pythonCmd) {
    $v = python --version 2>&1
    if ($v -match "3\.14") {
        Write-Host "ERROR: Python 3.14 detected — Playwright does NOT work with 3.14" -ForegroundColor Red
        Write-Host "Install Python 3.12 from https://www.python.org/downloads/" -ForegroundColor Yellow
        Write-Host "Then run:  py -3.12 -m venv .venv" -ForegroundColor Yellow
        exit 1
    }
    $pythonCmd = "python"
    Write-Host "Using: $v"
}

if (Test-Path ".venv") {
    Write-Host "Removing old .venv (may have wrong Python version)..."
    Remove-Item -Recurse -Force .venv
}

Write-Host "Creating virtual environment..."
Invoke-Expression "$pythonCmd -m venv .venv"

Write-Host "Activating .venv..."
& .\.venv\Scripts\Activate.ps1

Write-Host "Installing Python packages..."
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

Write-Host "Installing Playwright Chromium (no Google Chrome needed)..."
python -m playwright install chromium

if (-not (Test-Path ".env")) {
    Write-Host "Creating .env from .env.example..."
    Copy-Item .env.example .env
    Write-Host "Edit .env with your GA_URL, GA_EMAIL, GA_PASSWORD" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Setup complete ===" -ForegroundColor Green
python --version
Write-Host ""
Write-Host "In .env set:  BROWSER=chromium"
Write-Host ""
Write-Host "Run tests:"
Write-Host "  .\.venv\Scripts\Activate.ps1"
Write-Host "  python -m pytest tests/test_browser_only.py --headed -s -v"
