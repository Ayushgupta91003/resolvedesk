param([ValidateSet('gemini','openai','ollama')][string]$Provider = 'gemini')
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$envPath = Join-Path $projectRoot 'backend/.env'
$content = if(Test-Path -LiteralPath $envPath){ Get-Content -LiteralPath $envPath -Raw } else { Get-Content -LiteralPath (Join-Path $projectRoot 'backend/.env.example') -Raw }
function Set-Setting([string]$key, [string]$value) {
    $pattern = '(?m)^' + [regex]::Escape($key) + '=.*$'
    $entry = $key + '=' + $value
    if([regex]::IsMatch($script:content, $pattern)) { $script:content = [regex]::Replace($script:content, $pattern, [System.Text.RegularExpressions.MatchEvaluator]{ param($match) $entry }) }
    else { $script:content += "`n$entry`n" }
}
if($Provider -ne 'ollama') {
    Write-Host 'Paste your provider API key here. Input is hidden; it will not be printed.'
    $secret = Read-Host -AsSecureString 'API key'
    $pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
    try {
        $value = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer)
        if(-not $value -or $value.Trim().Length -lt 15) { throw 'No valid key was supplied. Existing settings were not changed.' }
        Set-Setting 'LLM_API_KEY' $value.Trim()
    } finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer); $value = $null }
}
Set-Setting 'AGENT_MODE' $(if($Provider -eq 'ollama'){'llm'}else{'demo'})
Set-Setting 'CLOUD_API_ENABLED' 'false'
Set-Setting 'LLM_PROVIDER' $Provider
Set-Setting 'LANGSMITH_TRACING' 'false'
switch($Provider) {
    'gemini' { Set-Setting 'OPENAI_MODEL' 'gemini-3.5-flash-lite'; Set-Setting 'LLM_BASE_URL' 'https://generativelanguage.googleapis.com/v1beta/openai/' }
    'openai' { Set-Setting 'OPENAI_MODEL' 'gpt-4.1-mini'; Set-Setting 'LLM_BASE_URL' 'https://api.openai.com/v1' }
    'ollama' { Set-Setting 'OPENAI_MODEL' 'resolvedesk-support'; Set-Setting 'LLM_BASE_URL' 'http://127.0.0.1:11434/v1' }
}
Set-Content -LiteralPath $envPath -Value $content.Trim() -Encoding utf8
$secret = $null
Write-Host "Saved $Provider settings to backend/.env. Cloud calls remain disabled until your billing tier is verified." -ForegroundColor Green
