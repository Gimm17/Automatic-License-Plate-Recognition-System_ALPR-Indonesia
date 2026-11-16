# Stream Simulator - Start Script
# Jalankan dari folder stream_simulator/

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  ALPR Stream Simulator" -ForegroundColor Cyan
Write-Host "  Upload video lalu lintas -> HLS Stream" -ForegroundColor Cyan
Write-Host "  Dashboard: http://localhost:9000" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

python app.py
