param(
    [string]$Board = "立体几何",
    [int]$BatchSize = 20,
    [int]$Limit = 0,
    [switch]$Append
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$BackendDir = Join-Path $ProjectRoot "backend"
$PythonExe = Join-Path $BackendDir ".venv\Scripts\python.exe"
$ScriptPath = Join-Path $BackendDir "rebuild_lesson_plan_vector_db.py"

if (-not (Test-Path -LiteralPath $PythonExe)) {
    throw "Missing python: $PythonExe"
}

if (-not (Test-Path -LiteralPath $ScriptPath)) {
    throw "Missing script: $ScriptPath"
}

$env:PYTHONIOENCODING = "utf-8"
$env:PYTHONUTF8 = "1"

$argsList = @(
    $ScriptPath
    "--collection", "math_resources"
    "--board", $Board
    "--batch-size", $BatchSize
)

if ($Limit -gt 0) {
    $argsList += @("--limit", $Limit)
}

if ($Append) {
    $argsList += "--append"
}

Write-Host "Import lesson plans into official math_resources..." -ForegroundColor Cyan
Write-Host "  Board: $Board"
Write-Host "  BatchSize: $BatchSize"
Write-Host "  Limit: $(if ($Limit -gt 0) { $Limit } else { 'ALL' })"
Write-Host "  Mode: $(if ($Append) { 'append' } else { 'reset collection' })"
Write-Host ""

& $PythonExe $argsList
if ($LASTEXITCODE -ne 0) {
    throw "Official import failed"
}

Write-Host ""
Write-Host "Official import finished. You can now start the backend and test dialogue retrieval." -ForegroundColor Green
