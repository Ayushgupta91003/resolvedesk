$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$statePath = Join-Path $projectRoot 'data/processes.json'
if (-not (Test-Path -LiteralPath $statePath)) { Write-Host 'No saved ResolveDesk processes.'; exit 0 }
$saved = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
foreach ($processId in @($saved.api, $saved.web)) {
    $processInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $processId" -ErrorAction SilentlyContinue
    if ($processInfo -and ($processInfo.CommandLine -match 'uvicorn app.main:app|next[/\\]dist[/\\]bin[/\\]next')) {
        Stop-Process -Id $processId -ErrorAction SilentlyContinue
    }
}
Write-Host 'ResolveDesk processes stopped. If a development child process remains, close its terminal.'
