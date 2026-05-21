param(
    [int]$BatchSize = 5,
    [int]$Total = 5
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

Write-Host "Running lesson plan rebuild in batches..." -ForegroundColor Cyan
Write-Host "  Python: $PythonExe"
Write-Host "  Script: $ScriptPath"
Write-Host "  BatchSize: $BatchSize"
Write-Host "  Total: $Total"
Write-Host ""

$startIndex = 0
while ($startIndex -lt $Total) {
    $limit = [Math]::Min($BatchSize, $Total - $startIndex)
    $collection = "lesson_plan_batch_$startIndex"
    Write-Host "==== Batch start=$startIndex limit=$limit ====" -ForegroundColor Yellow
    & $PythonExe $ScriptPath --start-index $startIndex --limit $limit --batch-size $limit --collection $collection
    if ($LASTEXITCODE -ne 0) {
        throw "Batch failed at start_index=$startIndex"
    }
    $startIndex += $limit
    Write-Host ""
}

Write-Host ""
Write-Host "Script finished. Copy the output back to me." -ForegroundColor Green
