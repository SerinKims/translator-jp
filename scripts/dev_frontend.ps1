[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version 2.0

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = (Resolve-Path (Join-Path $ScriptDir "..")).Path
$FrontendDir = Join-Path $ProjectRoot "frontend"
$FrontendEnvPath = Join-Path $FrontendDir ".env.local"

if (-not (Test-Path -LiteralPath $FrontendEnvPath)) {
    throw "frontend/.env.local이 없습니다. 먼저 .\scripts\setup.ps1을 실행해주세요."
}

$Pnpm = Get-Command "pnpm" -ErrorAction SilentlyContinue
if (-not $Pnpm) {
    throw "pnpm 명령을 찾을 수 없습니다. Node.js와 pnpm 설치 상태를 확인해주세요."
}

Set-Location -LiteralPath $FrontendDir
& $Pnpm.Source dev
