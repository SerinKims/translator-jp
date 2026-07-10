[CmdletBinding()]
param(
    [switch]$InstallPlaywright,
    [switch]$SkipDependencyInstall,
    [switch]$ForceDbInit,
    [string]$CondaEnv = "tr-jp",
    [switch]$UseVenv,
    [switch]$InstallBackendDependencies,
    [string]$CondaPythonVersion = "3.11"
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"
$VenvDir = Join-Path $BackendDir ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$BackendRequirements = Join-Path $BackendDir "requirements.txt"
$DbPath = Join-Path $BackendDir "translation.db"
$SchemaPath = Join-Path $BackendDir "app\db\schema.sql"
$RootEnvPath = Join-Path $ProjectRoot ".env"
$RootEnvExamplePath = Join-Path $ProjectRoot ".env.example"
$FrontendEnvPath = Join-Path $FrontendDir ".env.local"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Require-Command {
    param(
        [string]$Name,
        [string]$InstallHint
    )

    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $command) {
        throw "$Name 명령을 찾을 수 없습니다. $InstallHint"
    }
    return $command.Source
}

function Test-CondaEnv {
    param([string]$Name)

    $conda = Get-Command "conda" -ErrorAction SilentlyContinue
    if (-not $conda) {
        return $false
    }

    $envList = & $conda.Source --no-plugins env list 2>$null
    if ($LASTEXITCODE -ne 0) {
        return $false
    }

    return (($envList -join "`n") -match "(?m)^\s*$([regex]::Escape($Name))\s+")
}

function Invoke-ProjectPython {
    param([string[]]$Arguments)

    if ($script:UseCondaPython) {
        # conda run은 인자에 개행이 포함되면 실패한다
        # (AssertionError: Support for scripts where arguments contain newlines not implemented.)
        # "-c <multiline code>" 패턴이면 임시 .py 파일에 써서 그 파일을 실행하는 방식으로 우회한다.
        if (($Arguments.Count -eq 2) -and ($Arguments[0] -eq "-c") -and ($Arguments[1] -match "`n")) {
            $tempScript = [System.IO.Path]::GetTempFileName()
            $tempScript = [System.IO.Path]::ChangeExtension($tempScript, ".py")
            try {
                Set-Content -LiteralPath $tempScript -Encoding UTF8 -Value $Arguments[1]
                & $script:CondaPath --no-plugins run -n $script:CondaEnvName python $tempScript
            }
            finally {
                Remove-Item -LiteralPath $tempScript -ErrorAction SilentlyContinue
            }
        }
        else {
            & $script:CondaPath --no-plugins run -n $script:CondaEnvName python @Arguments
        }
    }
    else {
        & $script:ProjectPython @Arguments
    }
}

function Get-MissingRequirementSpecs {
    $checkCode = @"
from importlib import metadata
from pathlib import Path
import re

req_path = Path(r'''$BackendRequirements''')
missing = []

for raw in req_path.read_text(encoding='utf-8').splitlines():
    line = raw.strip()
    if not line or line.startswith('#') or line.startswith('-'):
        continue

    name = re.split(r'[<>=!~;\[]', line, 1)[0].strip()
    if not name:
        continue

    try:
        metadata.version(name.replace('_', '-'))
    except metadata.PackageNotFoundError:
        missing.append(line)

for spec in missing:
    print(spec)
"@

    $output = Invoke-ProjectPython -Arguments @("-c", $checkCode)
    if (-not $output) {
        return @()
    }
    return @($output | Where-Object { $_ -and $_.Trim() })
}

$CondaCommand = Get-Command "conda" -ErrorAction SilentlyContinue
$CondaPath = $null
if ($CondaCommand) {
    $CondaPath = $CondaCommand.Source
}
$CondaEnvName = $CondaEnv
$ProjectPython = $null

Write-Step "Preparing environment files"
if (-not (Test-Path -LiteralPath $RootEnvPath)) {
    Copy-Item -LiteralPath $RootEnvExamplePath -Destination $RootEnvPath
    Write-Host "Created .env from .env.example"
}
else {
    Write-Host ".env already exists"
}

if (-not (Test-Path -LiteralPath $FrontendEnvPath)) {
    Set-Content -LiteralPath $FrontendEnvPath -Encoding UTF8 -Value "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000"
    Write-Host "Created frontend/.env.local"
}
else {
    Write-Host "frontend/.env.local already exists"
}

if (-not $UseVenv) {
    Write-Step "Preparing conda environment"
    if (-not $CondaPath) {
        throw "conda 명령을 찾을 수 없습니다. conda를 설치하거나 .\run.ps1 -UseVenv 로 실행해주세요."
    }

    if (-not (Test-CondaEnv $CondaEnv)) {
        Write-Host "conda env '$CondaEnv'가 없어 새로 생성합니다."
        & $CondaPath --no-plugins create -y -n $CondaEnv "python=$CondaPythonVersion" pip
    }
    else {
        Write-Host "conda env '$CondaEnv' already exists"
    }

    $UseCondaPython = $true
}
else {
    $UseCondaPython = $false
}

if ($UseCondaPython) {
    Write-Step "Using conda environment"
    Write-Host "Using conda env: $CondaEnv"
    Write-Host "Backend Python dependencies will be checked inside conda env '$CondaEnv'."
}
else {
    Write-Step "Preparing backend virtual environment"
    $Python = Require-Command "python" "Python 3.11+ 설치 후 PATH에 추가해주세요."
    if (-not (Test-Path -LiteralPath $VenvPython)) {
        & $Python -m venv $VenvDir
        Write-Host "Created backend/.venv"
    }
    else {
        Write-Host "backend/.venv already exists"
    }
    $ProjectPython = $VenvPython
}

if (-not $SkipDependencyInstall) {
    Write-Step "Checking backend dependencies"
    $MissingRequirementSpecs = @(Get-MissingRequirementSpecs)
    if (($MissingRequirementSpecs.Count -gt 0) -or $InstallBackendDependencies) {
        if ($InstallBackendDependencies) {
            Write-Host "Installing backend requirements by request."
            Invoke-ProjectPython -Arguments @("-m", "pip", "install", "-r", $BackendRequirements)
        }
        else {
            Write-Host "Installing missing backend packages:"
            $MissingRequirementSpecs | ForEach-Object { Write-Host "  $_" }
            Invoke-ProjectPython -Arguments (@("-m", "pip", "install") + $MissingRequirementSpecs)
        }
    }
    else {
        Write-Host "Backend dependencies already look available."
    }
}
else {
    Write-Step "Skipping backend dependency install"
    Write-Host "Dependency installation was skipped by -SkipDependencyInstall."
}

Write-Step "Preparing database"
if ((-not (Test-Path -LiteralPath $DbPath)) -or $ForceDbInit) {
    $DbInitCode = @"
import sqlite3
from pathlib import Path

db_path = Path(r'''$DbPath''')
schema_path = Path(r'''$SchemaPath''')
schema = schema_path.read_text(encoding='utf-8')
with sqlite3.connect(db_path) as conn:
    conn.executescript(schema)
"@
    Invoke-ProjectPython -Arguments @("-c", $DbInitCode)
    Write-Host "Initialized backend/translation.db"
}
else {
    Write-Host "backend/translation.db already exists"
}

if ((-not $SkipDependencyInstall) -and (-not (Test-Path -LiteralPath (Join-Path $FrontendDir "node_modules")))) {
    Write-Step "Installing frontend dependencies"
    $Pnpm = Require-Command "pnpm" "Node.js와 pnpm 설치 상태를 확인해주세요."
    & $Pnpm --dir $FrontendDir install
}
elseif (-not $SkipDependencyInstall) {
    Write-Step "Skipping frontend dependency install"
    Write-Host "frontend/node_modules already exists."
}

if ($InstallPlaywright) {
    Write-Step "Installing Playwright Chromium"
    Invoke-ProjectPython -Arguments @("-m", "playwright", "install", "chromium")
}

Write-Host ""
Write-Host "Setup complete. Run .\scripts\dev.ps1 or .\run.ps1 to start the app." -ForegroundColor Green