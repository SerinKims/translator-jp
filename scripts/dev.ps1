[CmdletBinding()]
param(
    [switch]$SkipOllamaCheck,
    [string]$CondaEnv = "tr-jp",
    [switch]$UseVenv
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"
$BackendScript = Join-Path $ScriptDir "dev_backend.ps1"
$FrontendScript = Join-Path $ScriptDir "dev_frontend.ps1"
$VenvPython = Join-Path $BackendDir ".venv\Scripts\python.exe"

function Get-EnvValue {
    param(
        [string]$Name,
        [string]$DefaultValue
    )

    $value = $DefaultValue
    $envFiles = @(
        (Join-Path $ProjectRoot ".env"),
        (Join-Path $BackendDir ".env")
    )

    foreach ($envFile in $envFiles) {
        if (-not (Test-Path -LiteralPath $envFile)) {
            continue
        }

        foreach ($line in Get-Content -LiteralPath $envFile -Encoding UTF8) {
            if ($line -match "^\s*$([regex]::Escape($Name))\s*=\s*(.*)\s*$") {
                $value = $Matches[1].Trim().Trim('"').Trim("'")
            }
        }
    }

    return $value
}

function Test-PortAvailable {
    param([int]$Port)

    $listener = $null
    try {
        $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, $Port)
        $listener.Start()
        return $true
    }
    catch {
        return $false
    }
    finally {
        if ($listener) {
            $listener.Stop()
        }
    }
}

function Get-PowerShellExecutable {
    $pwsh = Get-Command "pwsh" -ErrorAction SilentlyContinue
    if ($pwsh) {
        return $pwsh.Source
    }

    $powershell = Get-Command "powershell" -ErrorAction SilentlyContinue
    if ($powershell) {
        return $powershell.Source
    }

    throw "PowerShell 실행 파일을 찾을 수 없습니다."
}

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
if ((-not $UseCondaPython) -and (-not (Test-Path -LiteralPath $VenvPython))) {
    throw "conda env '$CondaEnv' 또는 backend/.venv가 없습니다. 먼저 .\scripts\setup.ps1을 실행해주세요."
}

if (-not (Test-Path -LiteralPath (Join-Path $FrontendDir ".env.local"))) {
    throw "frontend/.env.local이 없습니다. 먼저 .\scripts\setup.ps1을 실행해주세요."
}

$BackendHost = Get-EnvValue "BACKEND_HOST" "0.0.0.0"
$BackendPort = [int](Get-EnvValue "BACKEND_PORT" "8000")
$FrontendPort = 3000
$ModelName = Get-EnvValue "OLLAMA_MODEL_NAME" "gemma4:26b-a4b-it-q4_K_M"

if (-not (Test-PortAvailable $BackendPort)) {
    Write-Warning "Backend port $BackendPort is already in use. 기존 서버가 떠 있는지 확인해주세요."
}

if (-not (Test-PortAvailable $FrontendPort)) {
    Write-Warning "Frontend port $FrontendPort is already in use. Next.js가 다른 포트를 사용할 수 있습니다."
}

if (-not $SkipOllamaCheck) {
    $Ollama = Get-Command "ollama" -ErrorAction SilentlyContinue
    if (-not $Ollama) {
        Write-Warning "ollama 명령을 찾을 수 없습니다. 번역 요청 전 로컬 Ollama 설치/실행 상태를 확인해주세요."
    }
    else {
        $OllamaList = & $Ollama.Source list 2>$null
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "ollama list 실행에 실패했습니다. Ollama 앱/서비스가 실행 중인지 확인해주세요."
        }
        elseif (($OllamaList -join "`n") -notmatch [regex]::Escape($ModelName)) {
            Write-Warning "$ModelName 모델을 찾지 못했습니다. 필요하면 ollama pull $ModelName 를 실행해주세요."
        }
    }
}

$PowerShellExe = Get-PowerShellExecutable

$BackendArgs = @(
    "-NoExit",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    $BackendScript,
    "-BindHost",
    $BackendHost,
    "-Port",
    $BackendPort,
    "-CondaEnv",
    $CondaEnv
)

if ($UseVenv) {
    $BackendArgs += "-UseVenv"
}

Start-Process -FilePath $PowerShellExe -WorkingDirectory $BackendDir -ArgumentList $BackendArgs

$FrontendArgs = @(
    "-NoExit",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    $FrontendScript
)

Start-Process -FilePath $PowerShellExe -WorkingDirectory $FrontendDir -ArgumentList $FrontendArgs

Write-Host ""
Write-Host "Started backend and frontend dev servers." -ForegroundColor Green
if ($UseCondaPython) {
    Write-Host "Backend Python: conda env '$CondaEnv'"
}
else {
    Write-Host "Backend Python: backend/.venv"
}
Write-Host "Frontend: http://localhost:3000"
Write-Host "Backend:  http://localhost:$BackendPort"
Write-Host "Stop servers by closing the two PowerShell windows or pressing Ctrl+C in each window."
