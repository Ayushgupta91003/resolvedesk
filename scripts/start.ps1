param([switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$projectPython = Join-Path $projectRoot '.venv/Scripts/python.exe'
$frontendRoot = Join-Path $projectRoot 'frontend'
$backendRoot = Join-Path $projectRoot 'backend'
$runtimeRoot = Join-Path $projectRoot 'data'
New-Item -ItemType Directory -Path $runtimeRoot -Force | Out-Null
if (-not (Test-Path -LiteralPath $projectPython) -or -not (Test-Path -LiteralPath (Join-Path $frontendRoot 'node_modules/next/dist/bin/next'))) {
    throw 'Dependencies are missing. Run ./scripts/setup.ps1 first.'
}
foreach ($port in @(8000, 3000)) {
    if (Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue) {
        throw "Port $port is already occupied. If ResolveDesk is already running, open http://127.0.0.1:3000."
    }
}
$env:DATA_DIR = Join-Path $runtimeRoot 'backend'
$apiArgs = @('-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', '8000')
if (Test-Path -LiteralPath (Join-Path $backendRoot '.env')) { $apiArgs += @('--env-file', '.env') }
$apiProcess = Start-Process -FilePath $projectPython -ArgumentList $apiArgs -WorkingDirectory $backendRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtimeRoot 'api.out.log') -RedirectStandardError (Join-Path $runtimeRoot 'api.err.log')
$webProcess = Start-Process -FilePath (Get-Command node).Source -ArgumentList @('node_modules/next/dist/bin/next', 'dev', '--hostname', '127.0.0.1', '--port', '3000') -WorkingDirectory $frontendRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtimeRoot 'web.out.log') -RedirectStandardError (Join-Path $runtimeRoot 'web.err.log')
@{ api = $apiProcess.Id; web = $webProcess.Id; api_started = $apiProcess.StartTime.ToUniversalTime().ToString('o'); web_started = $webProcess.StartTime.ToUniversalTime().ToString('o'); root = $projectRoot } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runtimeRoot 'processes.json')
Write-Host 'ResolveDesk is starting at http://127.0.0.1:3000' -ForegroundColor Green
Write-Host 'API docs: http://127.0.0.1:8000/docs'
Write-Host 'Demo owner: owner@orbit.demo / DemoPass123!'
Write-Host 'Logs: ./data/*.log | Stop: ./scripts/stop.ps1'
if (-not $NoBrowser) { Start-Process 'http://127.0.0.1:3000' }
