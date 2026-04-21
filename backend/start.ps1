# backend/start.ps1
# Start the FastAPI backend dev server with hot-reload.
# Run from project root: .\backend\start.ps1

$backendDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $backendDir

# Try venv activation
$venvPaths = @("venv\Scripts\Activate.ps1", ".venv\Scripts\Activate.ps1", "../venv/Scripts/Activate.ps1")
foreach ($p in $venvPaths) {
    if (Test-Path $p) {
        Write-Host "Activating venv: $p" -ForegroundColor Cyan
        & $p
        break
    }
}

Write-Host ""
Write-Host "Starting ALPR Indonesia Backend (FastAPI + Uvicorn)..." -ForegroundColor Green
Write-Host "  Docs:    http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "  Health:  http://localhost:8000/health" -ForegroundColor Yellow
Write-Host ""

python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level info
