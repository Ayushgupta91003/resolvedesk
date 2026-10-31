$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$frontendRoot = Join-Path $projectRoot 'frontend'
Push-Location -LiteralPath $frontendRoot
try {
    npm run build
    if ($LASTEXITCODE -ne 0) { throw 'Production build failed.' }
    $staticSource = Join-Path $frontendRoot '.next/static'
    $standaloneNext = Join-Path $frontendRoot '.next/standalone/.next'
    New-Item -ItemType Directory -Path $standaloneNext -Force | Out-Null
    Copy-Item -LiteralPath $staticSource -Destination $standaloneNext -Recurse -Force
    Write-Host 'Production build ready. START.cmd will use it; start.ps1 -Dev enables hot reload.' -ForegroundColor Green
} finally { Pop-Location }
