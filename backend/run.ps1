param(
  [int]$BackendPort = 8000
)

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

if (-not (Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
  Write-Host "Created .env from .env.example. Edit API keys as needed." -ForegroundColor Yellow
}

if (-not (Test-Path ".venv")) {
  Write-Host "Creating virtual environment..." -ForegroundColor Cyan
  py -3.11 -m venv .venv
}

$venvPath = Join-Path (Get-Location) ".venv\Scripts\Activate.ps1"
. $venvPath

python -m pip install --upgrade pip
pip install -r requirements.txt

Write-Host "Starting backend on port $BackendPort ..." -ForegroundColor Green
$env:UVICORN_RELOAD="true"
uvicorn app.main:app --host 0.0.0.0 --port $BackendPort --reload
