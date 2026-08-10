# setup_dev.ps1 — One-shot developer environment setup
# Run from the project root: .\scripts\setup_dev.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   RCI Code Equivalence Platform — Developer Setup        ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── Python venv ────────────────────────────────────────────────────────────────
Write-Host "► Setting up Python virtual environment..." -ForegroundColor Yellow
Set-Location "$ProjectRoot\backend"

if (-not (Test-Path ".venv")) {
    python -m venv .venv
    Write-Host "  ✓ Created .venv" -ForegroundColor Green
} else {
    Write-Host "  ✓ .venv already exists" -ForegroundColor Green
}

& ".venv\Scripts\Activate.ps1"
Write-Host "  ✓ Activated virtual environment" -ForegroundColor Green

Write-Host "► Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet
Write-Host "  ✓ Python dependencies installed" -ForegroundColor Green

# ── .env ──────────────────────────────────────────────────────────────────────
Set-Location $ProjectRoot
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "  ✓ Created .env from .env.example" -ForegroundColor Green
} else {
    Write-Host "  ✓ .env already exists" -ForegroundColor Green
}

# ── Frontend ──────────────────────────────────────────────────────────────────
Write-Host "► Installing frontend dependencies..." -ForegroundColor Yellow
Set-Location "$ProjectRoot\frontend"

if (-not (Test-Path "node_modules")) {
    npm install --silent
    Write-Host "  ✓ Node modules installed" -ForegroundColor Green
} else {
    Write-Host "  ✓ node_modules already exists" -ForegroundColor Green
}

# ── Summary ───────────────────────────────────────────────────────────────────
Set-Location $ProjectRoot
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Setup complete! Run the application:" -ForegroundColor Green
Write-Host ""
Write-Host "  Terminal 1 (backend):" -ForegroundColor Yellow
Write-Host "    cd backend" -ForegroundColor White
Write-Host "    .venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "    uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload" -ForegroundColor White
Write-Host ""
Write-Host "  Terminal 2 (frontend):" -ForegroundColor Yellow
Write-Host "    cd frontend" -ForegroundColor White
Write-Host "    npm run dev" -ForegroundColor White
Write-Host ""
Write-Host "  Open: http://127.0.0.1:5173" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════════" -ForegroundColor Cyan
