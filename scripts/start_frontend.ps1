# start_frontend.ps1 — Start the Vite dev server
# Run from project root: .\scripts\start_frontend.ps1

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location "$ProjectRoot\frontend"

if (-not (Test-Path "node_modules")) {
    Write-Host "⚠  node_modules not found. Run .\scripts\setup_dev.ps1 first." -ForegroundColor Yellow
    exit 1
}

Write-Host "► Starting Vite frontend on http://127.0.0.1:5173" -ForegroundColor Cyan
npm run dev
