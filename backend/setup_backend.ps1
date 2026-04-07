# ==============================================================================
# Trust Management App — backend setup and dev server (Windows PowerShell)
# ==============================================================================
# Prerequisites: Python 3.9.x or 3.10.x (TensorFlow 2.11 in this stack).
#
# Usage (from repo root):
#   pwsh -File .\backend\setup_backend.ps1
# Or from backend folder:
#   .\setup_backend.ps1
#
# Parameters:
#   -ReuseExistingVenv  Skip deleting/recreating venv; reuse if present (faster reruns).
#   -InstallOnly        Install/verify dependencies then exit (no uvicorn).
#   -FreePort8000       Stop whatever is listening on TCP 8000 before starting (optional).
#
# Environment:
#   TRUSTAPP_PYTHON     Full path to python.exe if the script cannot find 3.9/3.10.
#   GEMINI_API_KEY      Set in this shell, or put GEMINI_API_KEY=... in backend\.env
#                       (never commit .env or real keys).
# ==============================================================================

[CmdletBinding()]
param(
    [switch]$ReuseExistingVenv,
    [switch]$InstallOnly,
    [switch]$FreePort8000
)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

function Import-DotEnvIfMissing {
    param([string] $EnvFilePath)
    if (-not (Test-Path $EnvFilePath)) { return }
    Get-Content -LiteralPath $EnvFilePath -Encoding UTF8 | ForEach-Object {
        $line = $_.Trim()
        if (-not $line -or $line.StartsWith('#')) { return }
        $eq = $line.IndexOf('=')
        if ($eq -lt 1) { return }
        $name = $line.Substring(0, $eq).Trim()
        $val = $line.Substring($eq + 1).Trim()
        if (($val.Length -ge 2) -and (
                ($val.StartsWith('"') -and $val.EndsWith('"')) -or
                ($val.StartsWith("'") -and $val.EndsWith("'")))) {
            $val = $val.Substring(1, $val.Length - 2)
        }
        if (-not $name) { return }
        $current = [Environment]::GetEnvironmentVariable($name, 'Process')
        if ([string]::IsNullOrEmpty($current)) {
            [Environment]::SetEnvironmentVariable($name, $val, 'Process')
        }
    }
}

function Stop-ListenerOnPort {
    param([int] $Port)
    $pids = @(
        Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique
    )
    foreach ($procId in $pids) {
        if ($procId -and $procId -gt 0) {
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
    }
}

Import-DotEnvIfMissing (Join-Path $PSScriptRoot ".env")

function Resolve-CompatiblePythonPath {
    if ($env:TRUSTAPP_PYTHON -and (Test-Path -LiteralPath $env:TRUSTAPP_PYTHON)) {
        return $env:TRUSTAPP_PYTHON
    }

    $pyCmd = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCmd) {
        foreach ($pyVer in @("3.10", "3.9")) {
            try {
                $launcherPath = (& py "-$pyVer" -c "import sys; print(sys.executable)" 2>$null).Trim()
                if ($launcherPath -and (Test-Path -LiteralPath $launcherPath)) {
                    return $launcherPath
                }
            } catch {
            }
        }
    }

    $candidatePaths = @(
        "$env:USERPROFILE\AppData\Local\Programs\Python\Python310\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
        "$env:USERPROFILE\AppData\Local\Programs\Python\Python39\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python39\python.exe",
        "C:\Program Files\Python310\python.exe",
        "C:\Program Files\Python39\python.exe"
    )

    foreach ($candidate in $candidatePaths) {
        if (Test-Path -LiteralPath $candidate) {
            return $candidate
        }
    }

    return $null
}

# --- 1. Optional cleanup / venv ---
if ($FreePort8000) {
    Write-Host "--- Freeing port 8000 ---" -ForegroundColor Cyan
    Stop-ListenerOnPort -Port 8000
}

if (-not $ReuseExistingVenv) {
    Write-Host "--- 1. SCORCHED EARTH CLEANUP ---" -ForegroundColor Cyan
    if (Test-Path "venv") {
        Write-Host "Removing existing venv..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force venv
    }
} else {
    Write-Host "--- 1. REUSE MODE (keeping existing venv if present) ---" -ForegroundColor Cyan
}

$P39 = Resolve-CompatiblePythonPath

if (-not $P39) {
    Write-Host "ERROR: Could not find Python 3.10 or 3.9." -ForegroundColor Red
    Write-Host "Install from https://www.python.org/downloads/ (check 'Add to PATH'), or set:" -ForegroundColor Yellow
    Write-Host '  $env:TRUSTAPP_PYTHON = "C:\Path\To\Python310\python.exe"' -ForegroundColor Gray
    exit 1
}

$pyVersion = (& $P39 --version 2>&1)
if ($pyVersion -notmatch "Python 3\.(9|10)\.") {
    Write-Host "ERROR: This backend stack needs Python 3.10.x or 3.9.x; found: $pyVersion" -ForegroundColor Red
    Write-Host 'Point TRUSTAPP_PYTHON at a 3.10/3.9 python.exe, or use -ReuseExistingVenv only after a good venv exists.' -ForegroundColor Yellow
    exit 1
}
Write-Host "Using Python: $P39 ($pyVersion)" -ForegroundColor Green

# --- 2. Virtual environment ---
$venvPython = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $venvPython)) {
    Write-Host "--- 2. CREATING VENV ---" -ForegroundColor Green
    & $P39 -m venv venv
} else {
    Write-Host "--- 2. VENV ALREADY PRESENT ---" -ForegroundColor Green
}

$isolated_python = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
$isolated_pip    = Join-Path $PSScriptRoot "venv\Scripts\pip.exe"
$isolated_uvicorn = Join-Path $PSScriptRoot "venv\Scripts\uvicorn.exe"

if (-not (Test-Path -LiteralPath $isolated_python)) {
    Write-Host "ERROR: venv python missing at $isolated_python" -ForegroundColor Red
    exit 1
}

$env:PATH = "$(Join-Path $PSScriptRoot 'venv\Scripts');" + $env:PATH

# --- 3. Dependencies (pinned for TF 2.11 + protobuf descriptors) ---
Write-Host "--- 3. INSTALLING DEPENDENCIES ---" -ForegroundColor Cyan

& $isolated_python -m pip install --upgrade pip
Write-Host "Installing Protobuf 3.20.3..."
& $isolated_pip install "protobuf==3.20.3"
Write-Host "Installing NumPy 1.24.3..."
& $isolated_pip install "numpy==1.24.3"
Write-Host "Installing pandas..."
& $isolated_pip install "pandas"
Write-Host "Installing TensorFlow, Gemini SDK, FastAPI, LLM Guard, etc..."
& $isolated_pip install tensorflow==2.11.0 google-genai==0.3.0 fastapi uvicorn joblib h5py scikit-learn python-multipart llm-guard

if ([string]::IsNullOrWhiteSpace($env:GEMINI_API_KEY)) {
    Write-Host ""
    Write-Host "WARNING: GEMINI_API_KEY is not set. Gemini/LLM routes may fail." -ForegroundColor Yellow
    Write-Host "  Set it in this shell, or add backend\.env with: GEMINI_API_KEY=your_key" -ForegroundColor Gray
    Write-Host ""
}

Write-Host "--- 4. VERIFY IMPORTS ---" -ForegroundColor Magenta
$check_ver = & $isolated_python --version
Write-Host "Running on: $check_ver"
& $isolated_python -c "import tensorflow as tf; import google.genai; print('OK: TensorFlow', tf.__version__, '+ google.genai')"

if ($InstallOnly) {
    Write-Host "`nInstallOnly: skipping server. Start manually with:" -ForegroundColor Green
    Write-Host "  cd `"$PSScriptRoot`"" -ForegroundColor Gray
    Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor Gray
    Write-Host "  uvicorn main:app --reload --host 127.0.0.1 --port 8000" -ForegroundColor Gray
    exit 0
}

Write-Host "`n--- 5. STARTING SERVER ---" -ForegroundColor Green
Write-Host "http://127.0.0.1:8000  (Ctrl+C to stop)" -ForegroundColor Cyan
& $isolated_uvicorn main:app --reload --host 127.0.0.1 --port 8000

# Simulation (separate terminal):
#   .\venv\Scripts\python.exe ..\simulate_network.py
