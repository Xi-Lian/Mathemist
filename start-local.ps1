$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$EnvFile = Join-Path $ProjectRoot ".env"
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"
$BackendVenvPython = Join-Path $BackendDir ".venv\\Scripts\\python.exe"

if (-not (Test-Path -LiteralPath $EnvFile)) {
    throw "Missing env file: $EnvFile"
}

if (-not (Test-Path -LiteralPath $BackendDir)) {
    throw "Missing backend directory: $BackendDir"
}

if (-not (Test-Path -LiteralPath $FrontendDir)) {
    throw "Missing frontend directory: $FrontendDir"
}

function Import-DotEnv {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $lines = Get-Content -LiteralPath $Path
    foreach ($line in $lines) {
        $trimmed = $line.Trim()
        if ([string]::IsNullOrWhiteSpace($trimmed)) { continue }
        if ($trimmed.StartsWith("#")) { continue }

        if ($trimmed -match "^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)\s*$") {
            $name = $matches[1]
            $value = $matches[2].Trim()

            if ($value.Length -ge 2) {
                if (($value.StartsWith('"') -and $value.EndsWith('"')) -or
                    ($value.StartsWith("'") -and $value.EndsWith("'"))) {
                    $value = $value.Substring(1, $value.Length - 2)
                }
            }

            [Environment]::SetEnvironmentVariable($name, $value, "Process")
        }
    }
}

Import-DotEnv -Path $EnvFile

if (-not $env:HOST) { $env:HOST = "0.0.0.0" }
if (-not $env:PORT) { $env:PORT = "8000" }
if (-not $env:NEXT_PUBLIC_API_URL) { $env:NEXT_PUBLIC_API_URL = "http://localhost:$($env:PORT)" }
if (-not $env:NEXT_PUBLIC_ASSISTANT_ID) { $env:NEXT_PUBLIC_ASSISTANT_ID = "math-agent" }
if (-not $env:PYTHONIOENCODING) { $env:PYTHONIOENCODING = "utf-8" }
if (-not $env:PYTHONUTF8) { $env:PYTHONUTF8 = "1" }

if (Test-Path -LiteralPath $BackendVenvPython) {
    $PythonCmd = $BackendVenvPython
} else {
    $pythonFromPath = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonFromPath) {
        throw "python not found in PATH and backend\\.venv\\Scripts\\python.exe not found."
    }
    $PythonCmd = $pythonFromPath.Source
}

if (-not (Get-Command pnpm -ErrorAction SilentlyContinue)) {
    throw "pnpm not found in PATH."
}

# Backend python dependency precheck to avoid silent backend crash in spawned window
$provider = ($env:LLM_PROVIDER | ForEach-Object { $_.ToLowerInvariant().Trim() })
$requiredModules = @("fastapi", "langgraph", "markdown")
if ($provider -eq "openai_compatible") {
    $requiredModules += "langchain_openai"
} elseif ($provider -eq "deepseek") {
    $requiredModules += "langchain_deepseek"
}

$missingModules = @()
$nativeErrPrefVar = Get-Variable -Name PSNativeCommandUseErrorActionPreference -ErrorAction SilentlyContinue
if ($null -ne $nativeErrPrefVar) {
    $oldNativeErrPref = $PSNativeCommandUseErrorActionPreference
    $global:PSNativeCommandUseErrorActionPreference = $false
}

try {
    foreach ($module in $requiredModules) {
        $checkCode = "import importlib.util,sys; sys.exit(0 if importlib.util.find_spec('$module') else 1)"
        & $PythonCmd -c $checkCode 1>$null 2>$null
        if ($LASTEXITCODE -ne 0) {
            $missingModules += $module
        }
    }
} finally {
    if ($null -ne $nativeErrPrefVar) {
        $global:PSNativeCommandUseErrorActionPreference = $oldNativeErrPref
    }
}

if ($missingModules.Count -gt 0) {
    $missingText = [string]::Join(", ", $missingModules)
    throw "Missing backend python modules: $missingText. Run: cd backend; `"$PythonCmd`" -m pip install -r requirements.txt"
}

Write-Host "Startup config:" -ForegroundColor Cyan
Write-Host "  HOST=$($env:HOST)"
Write-Host "  PORT=$($env:PORT)"
Write-Host "  NEXT_PUBLIC_API_URL=$($env:NEXT_PUBLIC_API_URL)"
Write-Host "  NEXT_PUBLIC_ASSISTANT_ID=$($env:NEXT_PUBLIC_ASSISTANT_ID)"
Write-Host "  PYTHON=$PythonCmd"

Start-Process -FilePath "powershell.exe" -WorkingDirectory $BackendDir -ArgumentList @(
    "-NoExit",
    "-Command",
    "& '$PythonCmd' run_local.py"
)

Start-Process -FilePath "powershell.exe" -WorkingDirectory $FrontendDir -ArgumentList @(
    "-NoExit",
    "-Command",
    "pnpm dev"
)

Write-Host ""
Write-Host "Started two windows:" -ForegroundColor Green
Write-Host "  1) backend: python run_local.py"
Write-Host "  2) frontend: pnpm dev"
Write-Host ""
Write-Host "Backend URL: http://localhost:$($env:PORT)"
Write-Host "Frontend URL: http://localhost:3000"
