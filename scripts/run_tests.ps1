# run_tests.ps1 — Run pytest test suite
# Run from project root: .\scripts\run_tests.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Set-Location "$ProjectRoot\backend"

if (-not (Test-Path ".venv")) {
    Write-Host "⚠  Virtual environment not found. Run .\scripts\setup_dev.ps1 first." -ForegroundColor Yellow
    exit 1
}

& ".venv\Scripts\Activate.ps1"
Write-Host "► Running pytest..." -ForegroundColor Cyan
pytest -v --tb=short
