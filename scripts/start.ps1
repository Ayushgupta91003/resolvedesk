param([switch]$NoBrowser, [switch]$Dev)
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
$localEnvPath = Join-Path $backendRoot '.env'
if ((Test-Path -LiteralPath $localEnvPath) -and (Select-String -LiteralPath $localEnvPath -Pattern '^DATABASE_URL=.*(?:127\.0\.0\.1|localhost):55432/resolvedesk(?:\?|$)' -Quiet)) {
    Push-Location -LiteralPath $projectRoot
    try {
        docker compose -f compose.yaml -f compose.native.yaml up -d --wait db
        if ($LASTEXITCODE -ne 0) { throw 'ResolveDesk PostgreSQL could not start. Open Docker Desktop, wait for its engine, then retry START.cmd.' }
    } finally { Pop-Location }
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
$standalone = Join-Path $frontendRoot '.next/standalone/server.js'
if (-not $Dev -and (Test-Path -LiteralPath $standalone)) {
    $env:HOSTNAME = '127.0.0.1'
    $env:PORT = '3000'
    $webArgs = @('.next/standalone/server.js')
} else {
    $webArgs = @('node_modules/next/dist/bin/next', 'dev', '--hostname', '127.0.0.1', '--port', '3000')
}
$webProcess = Start-Process -FilePath (Get-Command node).Source -ArgumentList $webArgs -WorkingDirectory $frontendRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $runtimeRoot 'web.out.log') -RedirectStandardError (Join-Path $runtimeRoot 'web.err.log')
@{ api = $apiProcess.Id; web = $webProcess.Id; api_started = $apiProcess.StartTime.ToUniversalTime().ToString('o'); web_started = $webProcess.StartTime.ToUniversalTime().ToString('o'); root = $projectRoot } | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $runtimeRoot 'processes.json')
Write-Host 'Waiting for ResolveDesk to become ready...'
$deadline = [DateTime]::UtcNow.AddSeconds(45)
$ready = $false
while ([DateTime]::UtcNow -lt $deadline) {
    try {
        $health = Invoke-RestMethod 'http://127.0.0.1:8000/api/health' -TimeoutSec 1
        if ($health.status -eq 'ok') {
            $page = Invoke-WebRequest 'http://127.0.0.1:3000' -UseBasicParsing -TimeoutSec 2
            if ($page.StatusCode -eq 200) { $ready = $true; break }
        }
    } catch { }
    Start-Sleep -Milliseconds 300
}
if (-not $ready) { throw "Servers did not become ready within 45 seconds. Inspect $runtimeRoot for logs." }
Write-Host 'ResolveDesk is ready at http://127.0.0.1:3000' -ForegroundColor Green
Write-Host 'API docs: http://127.0.0.1:8000/docs'
Write-Host 'Demo owner: owner@orbit.demo / DemoPass123!'
Write-Host 'Logs: ./data/*.log | Stop: ./scripts/stop.ps1'
if (-not $NoBrowser) { Start-Process 'http://127.0.0.1:3000' }
