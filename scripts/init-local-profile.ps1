# Seed data/profiles/default from examples/data-profile (gitignored data/).
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$dest = Join-Path $root "data\profiles\default"
$src = Join-Path $root "examples\data-profile"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
foreach ($name in @("run.yaml", "script.yaml")) {
    $from = Join-Path $src $name
    $to = Join-Path $dest $name
    if (-not (Test-Path $to) -and (Test-Path $from)) {
        Copy-Item $from $to
        Write-Host "Copied $name -> $dest"
    } else {
        Write-Host "Skip $name (exists or missing source)"
    }
}
Write-Host "Local data root ready: $dest"
