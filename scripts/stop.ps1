$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$statePath = Join-Path $projectRoot 'data/processes.json'
if (-not (Test-Path -LiteralPath $statePath)) { Write-Host 'No saved ResolveDesk processes.'; exit 0 }
$saved = Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json
function Stop-OwnedTree([int]$processId) {
    $children = Get-CimInstance Win32_Process -Filter "ParentProcessId = $processId" -ErrorAction SilentlyContinue
    foreach ($child in $children) { Stop-OwnedTree $child.ProcessId }
    Stop-Process -Id $processId -ErrorAction SilentlyContinue
}
foreach ($kind in @('api', 'web')) {
    $processId = $saved.$kind
    $processInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $processId" -ErrorAction SilentlyContinue
    $startedKey = $kind + '_started'
    $process = Get-Process -Id $processId -ErrorAction SilentlyContinue
    $sameStart = $process -and $saved.$startedKey -and ([Math]::Abs(($process.StartTime.ToUniversalTime() - ([DateTime]$saved.$startedKey).ToUniversalTime()).TotalSeconds) -lt 1)
    if ($sameStart -and $processInfo -and ($processInfo.CommandLine -match 'uvicorn app.main:app|next[/\\]dist[/\\]bin[/\\]next|\.next[/\\]standalone[/\\]server.js')) {
        Stop-OwnedTree $processId
    }
}
Write-Host 'Owned ResolveDesk process trees stopped.'
