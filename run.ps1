[CmdletBinding()]
param(
    [switch]$SkipOllamaCheck,
    [string]$CondaEnv = "tr-jp",
    [switch]$UseVenv,
    [switch]$SkipSetup
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$SetupScript = Join-Path $ProjectRoot "scripts\setup.ps1"
$DevScript = Join-Path $ProjectRoot "scripts\dev.ps1"

function Test-CondaEnv {
    param([string]$Name)

    $conda = Get-Command "conda" -ErrorAction SilentlyContinue
    if (-not $conda) {
        return $false
    }

    $envList = & $conda.Source env list 2>$null
    if ($LASTEXITCODE -ne 0) {
        return $false
    }

    return (($envList -join "`n") -match "(?m)^\s*$([regex]::Escape($Name))\s+")
}

$UseCondaPython = (-not $UseVenv) -and (Test-CondaEnv $CondaEnv)

$RequiredPaths = @(
    (Join-Path $ProjectRoot ".env"),
    (Join-Path $ProjectRoot "backend\translation.db"),
    (Join-Path $ProjectRoot "frontend\.env.local"),
    (Join-Path $ProjectRoot "frontend\node_modules")
)

if (-not $UseCondaPython) {
    $RequiredPaths += (Join-Path $ProjectRoot "backend\.venv\Scripts\python.exe")
}

$Missing = @()
foreach ($path in $RequiredPaths) {
    if (-not (Test-Path -LiteralPath $path)) {
        $Missing += $path
    }
}

if ((-not $SkipSetup) -or ($Missing.Count -gt 0)) {
    if ($Missing.Count -gt 0) {
        Write-Host "First run detected. Running setup..." -ForegroundColor Cyan
    }
    else {
        Write-Host "Checking setup before start..." -ForegroundColor Cyan
    }
    & $SetupScript -CondaEnv $CondaEnv -UseVenv:$UseVenv
}
else {
    Write-Host "Setup already looks ready. Starting dev servers..." -ForegroundColor Cyan
}

& $DevScript -SkipOllamaCheck:$SkipOllamaCheck -CondaEnv $CondaEnv -UseVenv:$UseVenv
