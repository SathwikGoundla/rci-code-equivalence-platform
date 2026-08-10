# start_backend.ps1 — Start the FastAPI backend server
# Run from project root: .\scripts\start_backend.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Set-Location "$ProjectRoot\backend"

if (-not (Test-Path ".venv")) {
    Write-Host "⚠  Virtual environment not found. Run .\scripts\setup_dev.ps1 first." -ForegroundColor Yellow
    exit 1
}

& ".venv\Scripts\Activate.ps1"
Write-Host "► Starting FastAPI backend on http://127.0.0.1:8000" -ForegroundColor Cyan
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload --log-level info
