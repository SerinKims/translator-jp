[CmdletBinding()]
param(
    [string]$BindHost = "0.0.0.0",
    [int]$Port = 8000,
    [string]$CondaEnv = "tr-jp",
    [switch]$UseVenv
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path
$BackendDir = Join-Path $ProjectRoot "backend"
$VenvPython = Join-Path $BackendDir ".venv\Scripts\python.exe"

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

Set-Location -LiteralPath $BackendDir
$env:PYTHONPATH = $BackendDir

$Conda = Get-Command "conda" -ErrorAction SilentlyContinue
if ((-not $UseVenv) -and (Test-CondaEnv $CondaEnv)) {
    & $Conda.Source run -n $CondaEnv --no-capture-output python -m uvicorn app.main:app --host $BindHost --port $Port --reload
}
else {
    if (-not (Test-Path -LiteralPath $VenvPython)) {
        throw "conda env '$CondaEnv' 또는 backend/.venv를 찾지 못했습니다. 먼저 .\scripts\setup.ps1을 실행해주세요."
    }
    & $VenvPython -m uvicorn app.main:app --host $BindHost --port $Port --reload
}
