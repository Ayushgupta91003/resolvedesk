$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $projectRoot
Write-Host 'Preparing ResolveDesk (Python 3.12+, Node 20.9+ required)...' -ForegroundColor Green
if (-not (Test-Path '.venv/Scripts/python.exe')) {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'ensurepip was unavailable; bootstrapping with the system pip.'
    }
}
$projectPython = Join-Path $projectRoot '.venv/Scripts/python.exe'
& $projectPython -m pip --version 2>$null
if ($LASTEXITCODE -ne 0) {
    python -m pip --python $projectPython install pip
    if ($LASTEXITCODE -ne 0) { throw 'Could not bootstrap pip.' }
}
& $projectPython -m pip install -r backend/requirements.lock.txt
if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
Push-Location frontend
try {
    npm ci
    if ($LASTEXITCODE -ne 0) { throw 'Frontend dependency installation failed.' }
} finally { Pop-Location }
Write-Host 'Ready. Run ./scripts/start.ps1 or double-click START.cmd.' -ForegroundColor Green
