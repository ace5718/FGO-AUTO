# Create project venv and install fgo-auto (Windows / PowerShell)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

$VenvPython = Join-Path $Root "venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating venv at $Root\venv ..."
    python -m venv venv
}

Write-Host "Upgrading pip ..."
& $VenvPython -m pip install --upgrade pip

Write-Host "Installing fgo-auto [dev,windows] editable ..."
& $VenvPython -m pip install -e ".[dev,windows]"

Write-Host ""
Write-Host "Done. Activate with:"
Write-Host "  .\venv\Scripts\Activate.ps1"
Write-Host "Then run: fgo-auto version"
